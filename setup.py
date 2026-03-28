from setuptools import setup, find_packages

setup(
    name="agent-replay",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langgraph>=0.2.0",
        "langchain-core>=0.3.0",
        "rich>=13.7.0",
        "click>=8.1.7",
        "psycopg2-binary>=2.9.9",
    ],
    entry_points={
        "console_scripts": [
            "agent-replay=agent_replay.cli:cli",
        ],
    },
    python_requires=">=3.11",
)
