"""DevUI launch script — DEVELOPMENT USE ONLY.

Starts the MAF DevUI server so you can interactively inspect agents and workflows
in a browser UI at http://localhost:8080.

Run with:
    python app/ui/devui_app.py

DO NOT:
- Import this module from any other module.
- Include this file in the production Docker image CMD.
- Use this in CI/CD pipelines.
"""

if __name__ == "__main__":
    # Deferred imports so agent construction (and API-key validation) only
    # happens when this script is actually executed, not when it is imported.
    from agent_framework.devui import serve

    from app.agents.analyst_agent import analyst_agent
    from app.agents.orchestrator_agent import orchestrator_agent
    from app.agents.reviewer_agent import reviewer_agent
    from app.workflows.analysis_workflow import analysis_workflow

    serve(
        entities=[orchestrator_agent, analyst_agent, reviewer_agent, analysis_workflow],
        auto_open=True,
        port=8080,
    )
