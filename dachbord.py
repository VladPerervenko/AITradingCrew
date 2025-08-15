from jinja2 import Environment, FileSystemLoader
import os
import json
import glob

# Determine the absolute path to the directory containing this script
SCRIPT_DIR = "C:/Users/user/AITradingCrew"# os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, 'templates')
OUTPUT_DIR_MD = os.path.join(SCRIPT_DIR, 'reports_md')
AGENT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output', 'agents_output')

def load_symbols_data():
    """Loads trading data from JSON files in the agent output directory."""
    json_files = glob.glob(os.path.join(AGENT_OUTPUT_DIR, '*.json'))
    symbols_data = []
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Extract the relevant information. This part may need adjustment
                # based on the actual structure of your JSON files.
                symbol = os.path.basename(file_path).replace('.json', '')
                recommendation = data.get('recommendation', 'N/A')
                confidence = data.get('confidence_score', 'N/A')
                
                symbols_data.append({
                    "symbol": symbol.upper(),
                    "signal": recommendation,
                    "confidence": confidence,
                    "raw_output": json.dumps(data, indent=2)
                })
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {file_path}")
    return symbols_data

def generate_markdown_reports(symbols, template_name="report.md.j2"):
    """Generates individual Markdown reports for each symbol."""
    if not os.path.exists(TEMPLATES_DIR):
        print(f"Templates directory not found at {TEMPLATES_DIR}")
        return
        
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template(template_name)

    os.makedirs(OUTPUT_DIR_MD, exist_ok=True)

    for symbol_data in symbols:
        output_md = template.render(symbol_data)
        filename = f"{symbol_data['symbol']}_report.md"
        filepath = os.path.join(OUTPUT_DIR_MD, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(output_md)
        print(f"✅ Markdown report saved: {filepath}")

def generate_html_report(symbols, template_name="report.html.j2", output_file="dashboard.html"):
    """Generates a single HTML dashboard for all symbols."""
    if not os.path.exists(TEMPLATES_DIR):
        print(f"Templates directory not found at {TEMPLATES_DIR}")
        return

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template(template_name)
    output_html = template.render(symbols=symbols)

    output_filepath = os.path.join(SCRIPT_DIR, output_file)
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(output_html)
    print(f"✅ HTML dashboard saved: {output_filepath}")

if __name__ == "__main__":
    print("Generating reports from agent outputs...")
    actual_data = load_symbols_data()
    if actual_data:
        generate_html_report(actual_data)
        generate_markdown_reports(actual_data)
        print("\n✅ All reports generated successfully.")
    else:
        print("No data found in agent outputs. No reports were generated.")
