#!/usr/bin/env python
import asyncio
import warnings
import pytz
import datetime
from dotenv import load_dotenv
import typer
from typing_extensions import Annotated

from ai_trading_crew.config import settings
from ai_trading_crew.analysts.market_overview import HistoricalMarketFetcher
from ai_trading_crew.market_overview_agents import MarketOverviewAnalyst
from ai_trading_crew.stock_processor import process_stock_symbol
from ai_trading_crew.crew import StockComponentsSummarizeCrew
from ai_trading_crew.analysts.timegpt import get_timegpt_forecast

# Load environment variables
load_dotenv()

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create a Typer application
app = typer.Typer()


async def run_crew_async():
    """
    The core asynchronous function to run the crew.
    """
    print(f"Kicking off AI Trading Crew for symbols: {settings.SYMBOLS}")
    start_time = datetime.datetime.now()

    vix_data = HistoricalMarketFetcher().get_vix(days=30)
    global_market_data = HistoricalMarketFetcher().get_global_market(days=30)
    get_timegpt_forecast()

    market_analyst = MarketOverviewAnalyst()
    market_agent, market_task = market_analyst.get_agent_and_task()

    print(f"Processing market overview symbol: {settings.STOCK_MARKET_OVERVIEW_SYMBOL}")
    await process_stock_symbol(
        settings.STOCK_MARKET_OVERVIEW_SYMBOL,
        vix_data=vix_data,
        global_market_data=global_market_data,
        additional_agents=[market_agent],
        additional_tasks=[market_task]
    )
    print("Market overview processing complete.")

    print(f"Starting concurrent processing for {len(settings.SYMBOLS)} symbols...")
    tasks = [process_stock_symbol(symbol) for symbol in settings.SYMBOLS]
    await asyncio.gather(*tasks)

    end_time = datetime.datetime.now()
    print(f"\n🎉 Crew run complete. Total execution time: {end_time - start_time}")


@app.command()
def run():
    """Main entry point to run the full trading crew analysis."""
    asyncio.run(run_crew_async())


@app.command()
def train(n_iterations: Annotated[int, typer.Option(help="Number of training iterations")], 
          filename: Annotated[str, typer.Option(help="Filename to save the training data")]):
    """Train the crew for a given number of iterations."""
    print(f"Starting training for {n_iterations} iterations, saving to {filename}...")
    inputs = {
        'symbol': settings.SYMBOLS,
        'current_time_est': datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    StockComponentsSummarizeCrew().crew().train(
        n_iterations=n_iterations,
        filename=filename,
        inputs=inputs
    )
    print("Training complete.")


@app.command()
def replay(task_id: Annotated[str, typer.Argument(help="The ID of the task to replay")]):
    """Replay the crew execution from a specific task."""
    print(f"Replaying crew execution from task: {task_id}")
    StockComponentsSummarizeCrew().crew().replay(task_id=task_id)
    print("Replay complete.")


@app.command()
def test(n_iterations: Annotated[int, typer.Option(help="Number of test iterations")], 
         openai_model_name: Annotated[str, typer.Option(help="Name of the OpenAI model to use for testing")]):
    """Test the crew execution."""
    print(f"Starting test with {n_iterations} iterations using model {openai_model_name}...")
    inputs = {
        "topic": "AI LLMs"
    }
    StockComponentsSummarizeCrew().crew().test(
        n_iterations=n_iterations, 
        openai_model_name=openai_model_name, 
        inputs=inputs
    )
    print("Test complete.")


if __name__ == "__main__":
    app()
