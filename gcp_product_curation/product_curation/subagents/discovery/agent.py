from google.adk.agents.llm_agent import Agent,LlmAgent
from product_curation import config
from ...tools.my_agent_tools import MyAgentTools
from product_curation.tools import guideline_search_tool
from . import prompt
import logging
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents import ParallelAgent,SequentialAgent
import asyncio

logger = logging.getLogger(__name__)

def build_agents():
    shared_tools = MyAgentTools()


    feature_agent = LlmAgent(
        name="feature_agent",
        model=config.MODEL_NAME,
        description="Identifies and summarizes high-level features of the product being assessed, focusing on aspects relevant to enterprise use and organizational standards.",
        instruction=prompt.feature_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="features",
    )

    limitations_agent = LlmAgent(
        name="limitations_agent",
        model=config.MODEL_NAME,
        description="Identifies limitations and constraints of the product, especially those impacting security, compliance, data residency, networking, and compatibility with enterprise tooling.",
        instruction=prompt.limitations_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="limitations",
    )

    cmek_agent = LlmAgent(
        name="cmek_agent",
        model=config.MODEL_NAME,
        description="Assesses CMEK (Customer Managed Encryption Key) capabilities and their alignment with organizational security and compliance requirements.",
        instruction=prompt.cmek_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="cmek",
    )

    data_residency_agent = LlmAgent(
        name="data_residency_agent",
        model=config.MODEL_NAME,
        description="Evaluates data residency options and compliance, considering organizational policies and regulatory requirements.",
        instruction=prompt.data_residency_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="data_residency",
    )

    security_compliance_agent = LlmAgent(
        name="security_compliance_agent",
        model=config.MODEL_NAME,
        description="Reviews security, compliance, and custom organization constraints, focusing on preventative compliance and alignment with GCP custom org policies.",
        instruction=prompt.security_compliance_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="security_compliance",
    )

    iac_agent = LlmAgent(
        name="iac_agent",
        model=config.MODEL_NAME,
        description="Assesses Infrastructure as Code (IAC) support and suggests alternative solutions that align with organizational standards if native IAC is not available.",
        instruction=prompt.iac_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="iac",
    )

    network_agent = LlmAgent(
        name="network_agent",
        model=config.MODEL_NAME,
        description="Reviews network and connectivity requirements or capabilities, including architecture, interconnect options, and compatibility with enterprise networking standards.",
        instruction=prompt.network_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="network",
    )

    interconnect_agent = LlmAgent(
        name="interconnect_agent",
        model=config.MODEL_NAME,
        description="Assesses interconnect usage and options, considering organizational constraints and best practices.",
        instruction=prompt.interconnect_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="interconnect",
    )

    resilience_agent = LlmAgent(
        name="resilience_agent",
        model=config.MODEL_NAME,
        description="Strictly assesses Google Cloud product resiliency capabilities, focusing only on supported features such as high availability, scalability, disaster recovery, and business continuity as documented by Google Cloud. Avoids speculation or unsupported claims.",
        instruction=prompt.resilience_instruction,
        tools=[shared_tools],
        # output_key="resilience",
    )

    iam_agent = LlmAgent(
        name="iam_agent",
        model=config.MODEL_NAME,
        description="Reviews IAM requirements and capabilities, focusing on identity, authentication, and access management as per organizational standards.",
        instruction=prompt.iam_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="iam",
    )

    vpcsc_agent = LlmAgent(
        name="vpcsc_agent",
        model=config.MODEL_NAME,
        description="Strictly assesses Google Cloud VPC-SC (Virtual Private Cloud Service Controls) capabilities, focusing only on supported features, configuration options, limitations, and compliance as documented by Google Cloud. Avoids speculation or unsupported claims.",
        instruction=prompt.vpcsc_instruction,
        tools=[shared_tools, guideline_search_tool],
        # output_key="vpc_sc",
    )

    report_agent = LlmAgent(
        model=config.MODEL_NAME,
        name="ReportAgent",
        description="Compiles all sub-agent outputs into one discovery report.",
        instruction=prompt.REPORT_INSTRUCTION,
        output_key="product_assessment_template"
    )

    discovery_root_agent = ParallelAgent(
        # model=config.MODEL_NAME,
        name="DiscoveryAgent",
        description="Runs all discovery sub-agents in parallel and consolidates findings.",
        # instruction=prompt.DISCOVERY_AGENT_PROMPT,
        sub_agents=[
            feature_agent, limitations_agent, cmek_agent, data_residency_agent,
            security_compliance_agent, iac_agent, network_agent, interconnect_agent,
            resilience_agent, iam_agent, vpcsc_agent
        ]
    )

    # --- Sequential pipeline: run discovery first, then report ---
    orchestrator_agent = SequentialAgent(
        name="DiscoveryOrchestrator",
        description="Runs discovery in parallel first, then compiles into final report.",
        sub_agents=[discovery_root_agent, report_agent],
    )

    return orchestrator_agent, shared_tools


#********ADDED for DEBUGGING****************    
def debug_tools(agent, indent=0):
    tools = getattr(agent, "tools_dict", None)
    if tools is not None:
        print(" " * indent + f"{agent.name}: {list(tools.keys())}")
    else:
        print(" " * indent + f"{agent.name}: (no tools_dict)")
    for sub in getattr(agent, "sub_agents", []):
        debug_tools(sub, indent + 2)

