from html import escape
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


def install_docs(app: FastAPI):
    @app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
    def documentation():
        schema = app.openapi()
        rows = []
        for path, methods in schema["paths"].items():
            for method, op in methods.items():
                rows.append(
                    f"<tr><td>{escape(method.upper())}</td><td><code>{escape(path)}</code></td><td>{escape(op['summary'])}</td></tr>"
                )
        return (
            """<!doctype html><html lang="en"><title>ProcureFlow API</title><meta name="viewport" content="width=device-width,initial-scale=1">
        <style>body{font:16px system-ui;max-width:960px;margin:3rem auto;padding:0 1rem;color:#15352d}td,th{padding:.6rem;text-align:left;border-bottom:1px solid #dbe4df}table{border-collapse:collapse}</style>
        <h1>ProcureFlow API</h1><p>Use the OpenAPI contract for request schemas, response models and bearer authentication.</p>
        <p><a href="/openapi.json">OpenAPI JSON</a></p><table><tr><th>Method</th><th>Path</th><th>Operation</th></tr>"""
            + "".join(rows)
            + "</table></html>"
        )
