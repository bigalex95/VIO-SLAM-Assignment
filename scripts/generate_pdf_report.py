import markdown
from weasyprint import HTML
import os

def generate_pdf(input_md, output_pdf):
    print(f"Reading {input_md}...")
    with open(input_md, 'r', encoding='utf-8') as f:
        text = f.read()

    print("Converting Markdown to HTML...")
    html_content = markdown.markdown(text, extensions=['tables', 'fenced_code'])

    # Add some basic styling
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; margin: 40px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            h1 {{ border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
            h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 30px; }}
            code {{ background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
            pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            blockquote {{ border-left: 4px solid #ddd; padding-left: 15px; color: #777; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    print(f"Generating PDF to {output_pdf}...")
    HTML(string=styled_html, base_url=os.path.dirname(input_md)).write_pdf(output_pdf)
    print("Done.")

if __name__ == "__main__":
    workspace_root = "/home/bigalex95/Projects/challenges/VIO-SLAM-Assignment"
    input_path = os.path.join(workspace_root, "docs/technical_report.md")
    output_path = os.path.join(workspace_root, "docs/technical_report.pdf")
    
    generate_pdf(input_path, output_path)
