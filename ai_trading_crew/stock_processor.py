#!/usr/bin/env python
import asyncio
import datetime
import os
import json
import dataclasses

from ai_trading_crew.crew import StockComponentsSummarizeCrew, AiArticlesPickerCrew, DayTraderAdvisorCrew
from ai_trading_crew.analysts.social import get_stocktwits_context
from ai_trading_crew.analysts.technical_indicators import get_ti_context
from ai_trading_crew.utils.company_info import get_company_name
from ai_trading_crew.analysts.fundamental_analysis import get_fundamental_context
from ai_trading_crew.analysts.timegpt import format_timegpt_forecast, get_timegpt_forecast
from ai_trading_crew.config import settings, RELEVANT_ARTICLES_FILE, AGENT_INPUTS_FOLDER, AGENT_OUTPUTS_FOLDER
from ai_trading_crew.utils.dates import get_today_str, get_yesterday_str, get_yesterday_18_est, get_today_str_no_min
from ai_trading_crew.analysts.stock_headlines_fetcher import get_news_context
from ai_trading_crew.analysts.stock_articles_fetcher import get_stock_news


def _get_paths(symbol: str):
    """Creates and returns paths for input and output directories."""
    today_str_no_min = get_today_str_no_min()
    input_dir = os.path.join(AGENT_INPUTS_FOLDER, today_str_no_min)
    output_dir = os.path.join(AGENT_OUTPUTS_FOLDER, today_str_no_min, symbol)
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    return input_dir, output_dir


def _write_to_file(filepath: str, content: str):
    """Writes content to a file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


async def _gather_input_data(symbol: str, company_name: str, input_dir: str):
    """Gathers all necessary data for a stock symbol and saves it to files."""
    today_str = get_today_str()
    yesterday_str = get_yesterday_str()
    
    # Get and save stock headlines
    stock_headlines = get_news_context(symbol=symbol, start_time=f"{yesterday_str} 18:00")
    _write_to_file(os.path.join(input_dir, f"{symbol}_market_headlines.txt"), stock_headlines)

    # Run AiArticlesPickerCrew to select relevant articles
    picker_inputs = {'company_name': company_name, 'stock_headlines': stock_headlines, 'today_str': today_str}
    await AiArticlesPickerCrew(symbol).crew().kickoff_async(inputs=picker_inputs)

    # Get and save stock news from selected articles
    relevant_articles_file = os.path.join(input_dir, f"{symbol}_{RELEVANT_ARTICLES_FILE}")
    stock_news = await get_stock_news(symbol, relevant_articles_file)
    _write_to_file(os.path.join(input_dir, f"{symbol}_stock_news.txt"), stock_news)

    # Get and save other context data
    ti_data = get_ti_context(symbol=symbol)
    _write_to_file(os.path.join(input_dir, f"{symbol}_technical_indicators.txt"), ti_data)

    fundamental_data = get_fundamental_context(symbol=symbol)
    _write_to_file(os.path.join(input_dir, f"{symbol}_fundamental_analysis.txt"), fundamental_data)

    stocktwits_data = get_stocktwits_context(symbol, settings.SOCIAL_FETCH_LIMIT, get_yesterday_18_est())
    _write_to_file(os.path.join(input_dir, f"{symbol}_stocktwits.txt"), stocktwits_data)

    timegpt_forecasts = get_timegpt_forecast()
    timegpt_forecast = format_timegpt_forecast(timegpt_forecasts, symbol, company_name)
    _write_to_file(os.path.join(input_dir, f"{symbol}_timegpt_forecast.txt"), timegpt_forecast)

    return {
        'company_name': company_name,
        'stocktwits_data': stocktwits_data,
        'technical_indicator_data': ti_data,
        'fundamental_analysis_data': fundamental_data,
        'timegpt_forecast': timegpt_forecast,
        'stock_headlines': stock_headlines,
        'stock_news': stock_news,
        'today_str': today_str,
        'historical_days': 30
    }


async def _run_summary_crew(symbol: str, inputs: dict, additional_agents=None, additional_tasks=None):
    """Runs the StockComponentsSummarizeCrew."""
    inputs.update({
        'vix_data': inputs.get('vix_data', {}),
        'global_market_data': inputs.get('global_market_data', {})
    })
    await StockComponentsSummarizeCrew(
        symbol,
        additional_agents=additional_agents,
        additional_tasks=additional_tasks
    ).crew().kickoff_async(inputs=inputs)


def _read_summary_file(symbol_folder: str, filename: str) -> str:
    """Helper function to read summary files safely."""
    today_str_no_min = get_today_str_no_min()
    file_path = os.path.join(AGENT_OUTPUTS_FOLDER, today_str_no_min, symbol_folder, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Summary file not found at {file_path}. Returning empty string.")
        return ""


async def _run_advisor_crew(symbol: str, company_name: str):
    """Prepares inputs and runs the DayTraderAdvisorCrew."""
    # Read individual stock summaries
    news_summary = _read_summary_file(symbol, "news_summary_report.md")
    sentiment_summary = _read_summary_file(symbol, "sentiment_summary_report.md")
    technical_summary = _read_summary_file(symbol, "technical_indicator_summary_report.md")
    fundamental_summary = _read_summary_file(symbol, "fundamental_analysis_summary_report.md")
    timegpt_summary = _read_summary_file(symbol, "timegpt_forecast_summary_report.md")

    # Read market analysis summaries
    market_symbol = settings.STOCK_MARKET_OVERVIEW_SYMBOL
    market_news_summary = _read_summary_file(market_symbol, "news_summary_report.md")
    market_sentiment_summary = _read_summary_file(market_symbol, "sentiment_summary_report.md")
    market_technical_summary = _read_summary_file(market_symbol, "technical_indicator_summary_report.md")
    market_timegpt_summary = _read_summary_file(market_symbol, "timegpt_forecast_summary_report.md")
    market_overview_summary = _read_summary_file(market_symbol, "market_overview_summary_report.md")

    day_trader_inputs = {
        'company_name': company_name,
        'news_summary': news_summary,
        'sentiment_summary': sentiment_summary,
        'technical_summary': technical_summary,
        'fundamental_summary': fundamental_summary,
        'timegpt_summary': timegpt_summary,
        'market_news_summary': market_news_summary,
        'market_sentiment_summary': market_sentiment_summary,
        'market_technical_summary': market_technical_summary,
        'market_timegpt_summary': market_timegpt_summary,
        'market_overview_summary': market_overview_summary
    }

    return await DayTraderAdvisorCrew(symbol).crew().kickoff_async(inputs=day_trader_inputs)


def _save_final_result(symbol: str, result):
    """Saves the final result to a JSON file."""
    agents_output_path = os.path.join("output", "agents_output")
    os.makedirs(agents_output_path, exist_ok=True)
    
    # Ensure result is a serializable dictionary
    if dataclasses.is_dataclass(result):
        result_data = dataclasses.asdict(result)
    elif hasattr(result, 'dict'):
        result_data = result.dict()
    else:
        result_data = result

    filepath = os.path.join(agents_output_path, f"{symbol}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)


async def process_stock_symbol(symbol: str, vix_data=None, global_market_data=None, additional_agents=None, additional_tasks=None):
    """
    Process a stock symbol by gathering all necessary data and running the analysis crews.
    
    Args:
        symbol: Stock symbol to process
        vix_data: VIX data (optional, for market overview)
        global_market_data: Global market data (optional, for market overview)
        additional_agents: Additional agents for the crew (optional, for market overview)
        additional_tasks: Additional tasks for the crew (optional, for market overview)
    """
    print(f"[{datetime.datetime.now()}] Starting processing for symbol: {symbol}")
    
    company_name = get_company_name(symbol)
    input_dir, _ = _get_paths(symbol)

    # Step 1: Gather all input data
    final_inputs = await _gather_input_data(symbol, company_name, input_dir)
    final_inputs['vix_data'] = vix_data
    final_inputs['global_market_data'] = global_market_data

    # Step 2: Run the summarization crew
    await _run_summary_crew(symbol, final_inputs, additional_agents, additional_tasks)

    # Step 3: Run the final advisor crew
    day_trader_result = await _run_advisor_crew(symbol, company_name)

    # Step 4: Save the final result
    _save_final_result(symbol, day_trader_result)
    
    print(f"[{datetime.datetime.now()}] Finished processing for symbol: {symbol}")
    return day_trader_result


def process_stock_symbol_sync(symbol: str, vix_data=None, global_market_data=None, additional_agents=None, additional_tasks=None):
    """
    Synchronous wrapper for process_stock_symbol that maintains backward compatibility.
    """
    return asyncio.run(process_stock_symbol(symbol, vix_data, global_market_data, additional_agents, additional_tasks))