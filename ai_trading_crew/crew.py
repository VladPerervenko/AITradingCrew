from crewai import Agent, Crew, Process, Task
import os
import yaml
from ai_trading_crew.config import DEFAULT_STOCKTWITS_LLM, PROJECT_LLM, DEFAULT_TI_LLM, DEEPSEEK_OPENROUTER_LLM, AGENT_OUTPUTS_FOLDER, AGENT_INPUTS_FOLDER, RELEVANT_ARTICLES_FILE, LOG_FOLDER
from ai_trading_crew.utils.dates import get_today_str, get_yesterday_str, get_today_str_no_min

today_str = get_today_str()
yesterday_str = get_yesterday_str()
today_str_no_min = get_today_str_no_min()
yesterday_str = get_yesterday_str()
YESTERDAY_HOUR = "18:00"  # 6 PM EST
HISTORICAL_DAYS = 30


def ensure_log_date_folder():
	"""Ensure the log folder for today's date exists"""
	log_date_folder = os.path.join(LOG_FOLDER, today_str_no_min)
	if not os.path.exists(log_date_folder):
		os.makedirs(log_date_folder)
	return log_date_folder

class BaseCrewClass:
	"""Base class for all AI trading crews"""
	
	
	def __init__(self, symbol, stocktwit_llm=DEFAULT_STOCKTWITS_LLM, technical_ind_llm=DEFAULT_TI_LLM):
		self.symbol = symbol
		self.stocktwit_llm = stocktwit_llm
		self.technical_ind_llm = technical_ind_llm

class AiArticlesPickerCrew(BaseCrewClass):
	"""AiTradingCrew crew base"""
	def __init__(self, symbol, stocktwit_llm=DEFAULT_STOCKTWITS_LLM, technical_ind_llm=DEFAULT_TI_LLM):
		super().__init__(symbol, stocktwit_llm, technical_ind_llm)
		with open('ai_trading_crew/config/agents_article.yaml', 'r') as f:
			self.agents_config = yaml.safe_load(f)
		with open('ai_trading_crew/config/tasks_article.yaml', 'r') as f:
			self.tasks_config = yaml.safe_load(f)

	def relevant_news_filter_agent(self) -> Agent:
		agent_config = self.agents_config['relevant_news_filter_agent']
		return Agent(
			role=agent_config['role'],
			goal=agent_config['goal'],
			backstory=agent_config['backstory'],
			allow_delegation=agent_config['allow_delegation'],
			verbose=True,
			llm=DEEPSEEK_OPENROUTER_LLM
		)

	def relevant_news_filter_task(self) -> Task:
		task_config = self.tasks_config['relevant_news_filter_task']
		return Task(
			description=task_config['description'],
			expected_output=task_config['expected_output'],
			agent=self.relevant_news_filter_agent(),
			output_file=os.path.join(AGENT_INPUTS_FOLDER, today_str_no_min, f'{self.symbol}_{RELEVANT_ARTICLES_FILE}'),
			verbose=True
		)
	
	def crew(self) -> Crew:
		"""Creates the AiTradingCrew crew"""
		ensure_log_date_folder()
		return Crew(
			agents=[self.relevant_news_filter_agent()],
			tasks=[self.relevant_news_filter_task()],
			process='sequential',
			verbose=True
		)

class StockComponentsSummarizeCrew(BaseCrewClass):
	"""AiTradingCrew crew"""
	def __init__(self, symbol, stocktwit_llm=DEFAULT_STOCKTWITS_LLM, technical_ind_llm=DEFAULT_TI_LLM, additional_agents=None, additional_tasks=None):
		super().__init__(symbol, stocktwit_llm, technical_ind_llm)
		self.additional_agents = additional_agents or []
		self.additional_tasks = additional_tasks or []
		with open('ai_trading_crew/config/agents.yaml', 'r') as f:
			self.agents_config = yaml.safe_load(f)
		with open('ai_trading_crew/config/tasks.yaml', 'r') as f:
			self.tasks_config = yaml.safe_load(f)

	def news_summarizer_agent(self) -> Agent:
		agent_config = self.agents_config['news_summarizer_agent']
		return Agent(
			role=agent_config['role'],
			goal=agent_config['goal'],
			backstory=agent_config['backstory'],
			allow_delegation=agent_config['allow_delegation'],
			verbose=True,
			llm=DEEPSEEK_OPENROUTER_LLM
		)

	def sentiment_summarizer_agent(self) -> Agent:
		agent_config = self.agents_config['sentiment_summarizer_agent']
		return Agent(
			role=agent_config['role'],
			goal=agent_config['goal'],
			backstory=agent_config['backstory'],
			allow_delegation=agent_config['allow_delegation'],
			verbose=True,
			llm=self.stocktwit_llm
		)

	def technical_indicator_summarizer_agent(self) -> Agent:
		agent_config = self.agents_config['technical_indicator_summarizer_agent']
		return Agent(
			role=agent_config['role'],
			goal=agent_config['goal'],
			backstory=agent_config['backstory'],
			allow_delegation=agent_config['allow_delegation'],
			verbose=True,
			llm=self.technical_ind_llm
		)

	def fundamental_analysis_agent(self) -> Agent:
		agent_config = self.agents_config['fundamental_analysis_agent']
		return Agent(
			role=agent_config['role'],
			goal=agent_config['goal'],
			backstory=agent_config['backstory'],
			allow_delegation=agent_config['allow_delegation'],
			verbose=True,
			llm=PROJECT_LLM
		)

	def timegpt_analyst_agent(self) -> Agent:
		agent_config = self.agents_config['timegpt_analyst_agent']
		return Agent(
			role=agent_config['role'],
			goal=agent_config['goal'],
			backstory=agent_config['backstory'],
			allow_delegation=agent_config['allow_delegation'],
			verbose=True,
			llm=PROJECT_LLM
		)

	def news_summarization_task(self) -> Task:
		task_config = self.tasks_config['news_summarization_task']
		return Task(
			description=task_config['description'],
			expected_output=task_config['expected_output'],
			agent=self.news_summarizer_agent(),
			output_file=os.path.join(AGENT_OUTPUTS_FOLDER, today_str_no_min, self.symbol, 'news_summary_report.md'),
			verbose=True,
		)

	def sentiment_summarization_task(self) -> Task:
		task_config = self.tasks_config['sentiment_summarization_task']
		return Task(
			description=task_config['description'],
			expected_output=task_config['expected_output'],
			agent=self.sentiment_summarizer_agent(),
			output_file=os.path.join(AGENT_OUTPUTS_FOLDER, today_str_no_min, self.symbol, 'sentiment_summary_report.md'),
			verbose=True
		)

	def technical_indicator_summarization_task(self) -> Task:
		task_config = self.tasks_config['technical_indicator_summarization_task']
		return Task(
			description=task_config['description'],
			expected_output=task_config['expected_output'],
			agent=self.technical_indicator_summarizer_agent(),
			output_file=os.path.join(AGENT_OUTPUTS_FOLDER, today_str_no_min, self.symbol, 'technical_indicator_summary_report.md'),
			verbose=True
		)

	def fundamental_analysis_task(self) -> Task:
		task_config = self.tasks_config['fundamental_analysis_task']
		return Task(
			description=task_config['description'],
			expected_output=task_config['expected_output'],
			agent=self.fundamental_analysis_agent(),
			output_file=os.path.join(AGENT_OUTPUTS_FOLDER, today_str_no_min, self.symbol, 'fundamental_analysis_summary_report.md'),
			verbose=True
		)

	def timegpt_forecast_task(self) -> Task:
		task_config = self.tasks_config['timegpt_forecast_task']
		return Task(
			description=task_config['description'],
			expected_output=task_config['expected_output'],
			agent=self.timegpt_analyst_agent(),
			output_file=os.path.join(AGENT_OUTPUTS_FOLDER, today_str_no_min, self.symbol, 'timegpt_forecast_summary_report.md'),
			verbose=True,
		)

	def crew(self) -> Crew:
		"""Creates the AiTradingCrew crew"""
		ensure_log_date_folder()
		# Combine main agents/tasks with additional ones
		main_agents = [
			self.news_summarizer_agent(),
			self.sentiment_summarizer_agent(),
			self.technical_indicator_summarizer_agent(),
			self.fundamental_analysis_agent(),
			self.timegpt_analyst_agent()
		]
		main_tasks = [
			self.news_summarization_task(),
			self.sentiment_summarization_task(),
			self.technical_indicator_summarization_task(),
			self.fundamental_analysis_task(),
			self.timegpt_forecast_task()
		]
		
		all_agents = main_agents + self.additional_agents
		all_tasks = main_tasks + self.additional_tasks
		
		return Crew(
			agents=all_agents,
			tasks=all_tasks,
			process='sequential',  # Keep sequential for proper dependency handling
			verbose=True
		)

class DayTraderAdvisorCrew:
	"""Day Trader Advisor crew for making trading recommendations based on summaries"""
	
	def __init__(self, symbol):
		self.symbol = symbol
		# Load configurations
		config_dir = os.path.join(os.path.dirname(__file__), 'config')
		
		with open(os.path.join(config_dir, 'agents_day_trader.yaml'), 'r') as f:
			self.agents_config = yaml.safe_load(f)
		
		with open(os.path.join(config_dir, 'tasks_day_trader.yaml'), 'r') as f:
			self.tasks_config = yaml.safe_load(f)

	def day_trader_advisor_agent(self) -> Agent:
		agent_config = self.agents_config['day_trader_advisor_agent']
		return Agent(
			role=agent_config['role'],
			goal=agent_config['goal'],
			backstory=agent_config['backstory'],
			allow_delegation=agent_config['allow_delegation'],
			verbose=True,
			llm=DEEPSEEK_OPENROUTER_LLM
		)

	def day_trader_recommendation_task(self) -> Task:
		task_config = self.tasks_config['day_trader_recommendation_task']
		return Task(
			description=task_config['description'],
			expected_output=task_config['expected_output'],
			agent=self.day_trader_advisor_agent(),
			output_file=os.path.join(AGENT_OUTPUTS_FOLDER, today_str_no_min, self.symbol, 'day_trading_recommendation.md'),
			verbose=True
		)

	def crew(self) -> Crew:
		"""Creates the Day Trader Advisor crew"""
		ensure_log_date_folder()
		return Crew(
			agents=[self.day_trader_advisor_agent()],
			tasks=[self.day_trader_recommendation_task()],
			process='sequential',
			verbose=True
		)
