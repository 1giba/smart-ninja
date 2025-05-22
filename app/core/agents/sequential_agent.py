"""
Sequential Agent Pipeline controller.

This module implements a sequential agent pipeline that orchestrates the execution
of multiple agents in sequence: planning, scraping, analysis, and recommendation.
"""
import logging
import traceback
from typing import Any, Dict

from app.core.agents.analysis_agent import AnalysisAgent
from app.core.agents.base_agent import BaseAgent
from app.core.agents.notification_agent import NotificationAgent
from app.core.agents.planning_agent import PlanningAgent
from app.core.agents.recommendation_agent import RecommendationAgent
from app.core.agents.scraping_agent import ScrapingAgent


class SequentialAgent(BaseAgent):
    """
    Agent that orchestrates a sequential pipeline of agents.

    This agent controls the flow of execution through a series of agents,
    ensuring each agent's output is properly passed to the next agent.
    """

    def __init__(
        self,
        planning_agent: PlanningAgent,
        scraping_agent: ScrapingAgent,
        analysis_agent: AnalysisAgent,
        recommendation_agent: RecommendationAgent,
        notification_agent: NotificationAgent = None,
    ):
        """
        Initialize sequential agent with required child agents.

        Args:
            planning_agent: Agent for determining target websites
            scraping_agent: Agent for retrieving price data
            analysis_agent: Agent for analyzing price data
            recommendation_agent: Agent for generating recommendations
            notification_agent: Optional agent for triggering price alerts
        """
        self._planning_agent = planning_agent
        self._scraping_agent = scraping_agent
        self._analysis_agent = analysis_agent
        self._recommendation_agent = recommendation_agent
        self._notification_agent = notification_agent

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete agent pipeline in sequence.

        Args:
            input_data: Dictionary containing initial input data (model, country)

        Returns:
            Dictionary with final pipeline results or error information
        """
        try:
            # Step 1: Planning - determine target websites
            planning_result = await self._planning_agent.execute(input_data)

            # Validate planning output
            if not planning_result.get("websites", []):
                return {
                    "error": "No websites found for scraping",
                    "data": planning_result,
                }

            # Step 2: Scraping - retrieve price data from websites
            scraping_result = await self._scraping_agent.execute(planning_result)

            # Validate scraping output
            if not scraping_result:
                return {"error": "No price data found", "data": scraping_result}

            # Step 3: Analysis - analyze price data
            analysis_result = await self._analysis_agent.execute(scraping_result)

            # Make sure the price data is included for the recommendation agent
            if "price_data" not in analysis_result:
                analysis_result["price_data"] = scraping_result

            # Step 4: Recommendation - generate best offer recommendation
            recommendation_result = await self._recommendation_agent.execute(analysis_result)

            # Include all results in the final output for traceability
            recommendation_result["model"] = input_data.get("model")
            recommendation_result["country"] = input_data.get("country")
            recommendation_result["website_count"] = len(
                planning_result.get("websites", [])
            )
            recommendation_result["data_points"] = len(scraping_result)

            # Include key analysis metrics
            recommendation_result["average_price"] = analysis_result.get(
                "average_price"
            )
            recommendation_result["price_range"] = analysis_result.get("price_range")
            if "price_trend" in analysis_result:
                recommendation_result["price_trend"] = analysis_result.get(
                    "price_trend"
                )

            # Step 5 (Optional): Notification - check for price alerts
            if self._notification_agent:
                try:
                    # Make sure we include price data in the notification input
                    if (
                        "price_data" not in recommendation_result
                        and "price_data" in analysis_result
                    ):
                        recommendation_result["price_data"] = analysis_result[
                            "price_data"
                        ]

                    notification_result = await self._notification_agent.execute(
                        recommendation_result
                    )

                    # Include notification results in the final output
                    if notification_result.get("alerts_triggered"):
                        recommendation_result["alerts"] = notification_result[
                            "alerts_triggered"
                        ]

                    # Include any notification errors
                    if notification_result.get("notification_errors"):
                        recommendation_result[
                            "notification_errors"
                        ] = notification_result["notification_errors"]

                except Exception as notification_error:
                    # Log notification errors but don't fail the entire pipeline
                    logging.error(
                        "Error in notification stage: %s", str(notification_error)
                    )
                    recommendation_result["notification_error"] = str(
                        notification_error
                    )

            return recommendation_result

        except Exception as error:
            # Identify which stage failed
            stage = "unknown"
            # We need to check if variables exist AND if they were assigned values
            if not "planning_result" in locals():
                stage = "planning"
            elif not "scraping_result" in locals():
                stage = "scraping"
            elif not "analysis_result" in locals():
                stage = "analysis"
            else:
                stage = "recommendation"

            # Log the error
            logging.error("Error in %s stage: %s", stage, str(error))

            # Return error information
            return {
                "error": f"Error in {stage} stage: {str(error)}",
                "traceback": traceback.format_exc(),
            }
