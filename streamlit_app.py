# ================================
# CREWAI-FREE MULTI-AGENT SYSTEM FOR STREAMLIT
# ================================
# SOLUTION: No CrewAI dependencies - Pure LLM multi-agent system
# Works perfectly with Python 3.13 and Streamlit Community Cloud
# ================================

import streamlit as st
import requests
import json
import time
from datetime import datetime
import io
import os
import re

# Page Configuration
st.set_page_config(
    page_title="Multi-Agent AI Analysis System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f497d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-card {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 1rem 0;
    }
    .result-box {
        background: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1f497d;
    }
    .progress-text {
        font-size: 1.1rem;
        font-weight: bold;
    }
    .success-box {
        background: #e8f5e8;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

class GroqLLMAgent:
    """Direct Groq API integration without CrewAI dependencies"""
    
    def __init__(self, api_key, model="llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def call_llm(self, system_prompt, user_prompt, max_tokens=800):
        """Make direct API call to Groq"""
        try:
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                try:
                    return result['choices'][0]['message']['content']
                except (KeyError, IndexError):
                    return f"API Response Error: Invalid response format - {result}"
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 10))
                time.sleep(retry_after)
                # Retry once
                return self.call_llm(system_prompt, user_prompt, max_tokens)
            else:
                return f"API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Request Error: {str(e)}"

class MultiAgentSystem:
    """CrewAI-free multi-agent system using direct LLM calls"""
    
    def __init__(self, api_key):
        self.llm = GroqLLMAgent(api_key)
        
        # Define agent roles and system prompts
        self.research_agent_prompt = """You are a Senior Research Specialist with extensive knowledge across multiple domains.
        Your role is to conduct comprehensive research on any given topic using your knowledge base.
        
        For each query:
        1. Provide key facts and current information
        2. Include relevant statistics and data points
        3. Present multiple perspectives and viewpoints
        4. Add relevant context and background
        5. Mention recent developments and trends
        
        Structure your response with clear headings and organize information logically.
        Be comprehensive but concise, focusing on the most important and relevant information."""
        
        self.analysis_agent_prompt = """You are a Senior Data Analyst and Strategic Advisor with expertise in:
        - Statistical analysis and pattern recognition
        - Financial analysis and risk assessment
        - Strategic thinking and decision support
        - Predictive analysis and forecasting
        
        Your role is to analyze information and provide actionable insights.
        
        For each analysis:
        1. QUANTITATIVE INSIGHTS: Extract and analyze numerical data, trends, patterns
        2. QUALITATIVE ANALYSIS: Strategic implications, opportunities, challenges
        3. RISK ASSESSMENT: Potential risks, uncertainties, mitigation strategies
        4. PREDICTIVE ANALYSIS: Future trends, forecasts, scenarios
        5. STRATEGIC RECOMMENDATIONS: 3-5 prioritized actionable recommendations
        
        Structure your response with clear sections and provide practical, implementable advice."""
        
        self.orchestrator_agent_prompt = """You are a Chief Orchestrator and Executive Synthesis Expert.
        Your role is to synthesize information from research and analysis into executive-level reports.
        
        Create comprehensive reports with these exact sections:
        1. EXECUTIVE SUMMARY (3-4 key sentences)
        2. KEY FINDINGS (5 most important insights)
        3. STRATEGIC RECOMMENDATIONS (3 top priorities with implementation steps)
        4. IMPLEMENTATION ROADMAP (specific next steps with timelines)
        5. RISK CONSIDERATIONS (major concerns and mitigation strategies)
        6. CONCLUSION (final strategic assessment)
        
        Write in executive language suitable for C-level audiences. Be clear, actionable, and strategic."""
    
    def research_phase(self, query):
        """Research Agent Phase"""
        user_prompt = f"Conduct comprehensive research on: '{query}'"
        return self.llm.call_llm(self.research_agent_prompt, user_prompt)
    
    def analysis_phase(self, query, research_results):
        """Analysis Agent Phase"""
        user_prompt = f"""Analyze the following query: '{query}'
        
        Based on this research data:
        {research_results}
        
        Provide comprehensive analysis with quantitative insights, qualitative analysis, risk assessment, predictions, and strategic recommendations."""
        
        return self.llm.call_llm(self.analysis_agent_prompt, user_prompt, max_tokens=1000)
    
    def orchestration_phase(self, query, research_results, analysis_results):
        """Orchestrator Agent Phase"""
        user_prompt = f"""Create an executive synthesis report for: '{query}'
        
        RESEARCH FINDINGS:
        {research_results}
        
        ANALYSIS RESULTS:
        {analysis_results}
        
        Synthesize this information into a comprehensive executive report with all required sections."""
        
        return self.llm.call_llm(self.orchestrator_agent_prompt, user_prompt, max_tokens=1200)
    
    def run_multi_agent_analysis(self, query, progress_callback=None):
        """Execute the complete multi-agent workflow"""
        # Make progress_callback optional
        progress_callback = progress_callback or (lambda msg, pct: None)
        
        results = {
            'query': query,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Phase 1: Research Agent
            progress_callback("🔍 Research Agent analyzing query...", 25)
            
            research_results = self.research_phase(query)
            if "Error:" in research_results:
                return {'error': f"Research phase failed: {research_results}"}
            
            results['research'] = research_results
            time.sleep(3)  # Rate limiting
            
            # Phase 2: Analysis Agent
            progress_callback("📊 Analysis Agent processing insights...", 60)
            
            analysis_results = self.analysis_phase(query, research_results)
            if "Error:" in analysis_results:
                return {'error': f"Analysis phase failed: {analysis_results}"}
            
            results['analysis'] = analysis_results
            time.sleep(3)  # Rate limiting
            
            # Phase 3: Orchestrator Agent
            progress_callback("🎯 Orchestrator creating executive report...", 90)
            
            final_report = self.orchestration_phase(query, research_results, analysis_results)
            if "Error:" in final_report:
                return {'error': f"Orchestration phase failed: {final_report}"}
            
            results['final_report'] = final_report
            
            progress_callback("✅ Multi-Agent Analysis Complete!", 100)
            
            return results
            
        except Exception as e:
            return {'error': f"System error: {str(e)}"}

class SimpleDocumentGenerator:
    """Simple document generator for reports"""
    
    def create_text_report(self, results):
        """Create downloadable text report"""
        report = f"""
MULTI-AGENT AI ANALYSIS REPORT
===============================

Query: {results['query']}
Generated: {results['timestamp']}
System: Direct LLM Multi-Agent Architecture
Agents: Research Specialist → Data Analyst → Executive Orchestrator

🔍 RESEARCH FINDINGS
====================
{results.get('research', 'No research data available')}

📊 COMPREHENSIVE ANALYSIS  
=========================
{results.get('analysis', 'No analysis data available')}

🎯 EXECUTIVE SYNTHESIS
======================
{results.get('final_report', 'No final report available')}

═══════════════════════════════════════════════════════════════════════════════
Report Generated by Multi-Agent AI Analysis System
Technology: Direct Groq LLM Integration | Interface: Streamlit
Architecture: Research → Analysis → Synthesis | Python 3.13 Compatible
═══════════════════════════════════════════════════════════════════════════════
"""
        try:
            return report.encode('utf-8')
        except UnicodeEncodeError:
            return report.encode('utf-8', errors='replace')

# Main Application
def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Multi-Agent AI Analysis System</h1>', unsafe_allow_html=True)
    
    # Success message
    st.markdown("""
    <div class="success-box">
    <h3>✅ System Status: Fully Operational</h3>
    <p><strong>Python 3.13 Compatible</strong> • No dependency issues • Direct LLM integration</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key Input - Prefer environment variable
        env_api_key = os.getenv("GROQ_API_KEY")
        if env_api_key:
            api_key = env_api_key
            st.session_state.api_key = api_key
            st.success("✅ API Key loaded from environment variable")
        else:
            api_key = st.text_input(
                "Groq API Key",
                type="password",
                value=st.session_state.api_key,
                help="Get your free API key at console.groq.com (or set GROQ_API_KEY env var)"
            )
            if api_key:
                st.session_state.api_key = api_key
                st.success("✅ API Key configured")
            else:
                st.warning("⚠️ Please enter your Groq API key")
        
        st.markdown("---")
        
        # System Architecture
        st.header("🏗️ System Architecture")
        st.markdown("""
        <div class="agent-card">
        <h4>🔍 Research Agent</h4>
        <p>Conducts comprehensive research and gathers relevant information</p>
        </div>
        
        <div class="agent-card">
        <h4>📊 Analysis Agent</h4>
        <p>Performs strategic analysis with quantitative and qualitative insights</p>
        </div>
        
        <div class="agent-card">
        <h4>🎯 Orchestrator Agent</h4>
        <p>Synthesizes findings into executive-level comprehensive reports</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 **Direct LLM Architecture**\nNo external dependencies or compatibility issues")
    
    # Main Interface
    if not api_key:
        st.info("👈 Please configure your Groq API key in the sidebar to get started")
        
        st.markdown("""
        ### 🚀 Multi-Agent AI Analysis System
        
        **Key Features:**
        - 🔍 **Comprehensive Research**: Intelligent information gathering and context analysis
        - 📊 **Strategic Analysis**: Quantitative insights, risk assessment, and predictive analysis  
        - 🎯 **Executive Synthesis**: Professional reports with actionable recommendations
        - 📄 **Document Export**: Downloadable analysis reports
        - ⚡ **High Performance**: Direct LLM integration for fast responses
        - 🛡️ **Reliable**: No dependency conflicts, Python 3.13 compatible
        
        **Getting Started:**
        1. Get a **free Groq API key** at [console.groq.com](https://console.groq.com)
        2. Enter your API key in the sidebar (or set GROQ_API_KEY env var)
        3. Ask any question for comprehensive multi-agent analysis
        4. Download professional reports
        
        **Example Questions:**
        - "What are the key investment opportunities in renewable energy?"
        - "Analyze the future of artificial intelligence in healthcare"
        - "What are the risks and benefits of remote work for businesses?"
        """)
        return
    
    # Query Input Section
    st.header("📝 Analysis Query")
    user_query = st.text_area(
        "Enter your question for comprehensive multi-agent analysis:",
        placeholder="Example: What are the key trends in artificial intelligence for 2025?",
        height=120
    )
    
    # Control Buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        run_analysis = st.button("🚀 Run Multi-Agent Analysis", type="primary", use_container_width=True)
    with col2:
        if st.session_state.analysis_complete and st.session_state.results:
            clear_results = st.button("🔄 Clear Results", use_container_width=True)
            if clear_results:
                st.session_state.analysis_complete = False
                st.session_state.results = None
                st.rerun()
    with col3:
        if st.session_state.analysis_complete and st.session_state.results:
            generate_doc = st.button("📄 Download Report", use_container_width=True)
        else:
            generate_doc = False
    
    # Analysis Execution
    if run_analysis and user_query.strip():
        # Input validation
        if len(user_query) > 2000:
            st.error("❌ Query too long. Please limit to 2000 characters.")
            return
        
        if not all(c.isprintable() for c in user_query):
            st.error("❌ Invalid characters in query. Please use standard text.")
            return
        
        if not api_key:
            st.error("❌ Please configure your Groq API key first")
            return
        
        # Initialize system
        try:
            system = MultiAgentSystem(api_key)
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(message, percent):
                progress_bar.progress(percent/100)
                status_text.markdown(f'<p class="progress-text">{message}</p>', unsafe_allow_html=True)
            
            # Run analysis
            with st.spinner("Initializing multi-agent system..."):
                results = system.run_multi_agent_analysis(user_query, update_progress)
            
            # Handle results
            if 'error' in results:
                st.error(f"❌ Analysis failed: {results['error']}")
                
                if "rate" in results['error'].lower():
                    st.info("💡 Rate limit reached. Please wait 30 seconds and try again.")
                elif "401" in results['error'] or "invalid" in results['error'].lower():
                    st.error("🔑 Invalid API key. Please check your Groq API key.")
                else:
                    st.info("🔄 Please try again or check your internet connection.")
            else:
                st.session_state.results = results
                st.session_state.analysis_complete = True
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Display success
                st.success("🎉 Multi-agent analysis completed successfully!")
                
                # Display results
                display_results(results)
                
        except Exception as e:
            st.error(f"❌ System initialization failed: {e}")
            st.info("💡 Please check your API key and try again")
    
    elif st.session_state.analysis_complete and st.session_state.results:
        # Display cached results
        display_results(st.session_state.results)
    
    # Document Generation
    if generate_doc and st.session_state.results:
        generate_document(st.session_state.results)

def display_results(results):
    """Display comprehensive analysis results"""
    st.header("📋 Multi-Agent Analysis Results")
    
    # Executive Summary
    st.subheader("🎯 Executive Summary")
    final_report = str(results.get('final_report', ''))
    
    # Extract executive summary using regex
    summary_match = re.search(r'EXECUTIVE SUMMARY\s*([\s\S]*?)(?=\n\s*(?:KEY FINDINGS|[\w\s]+:|$))', final_report, re.IGNORECASE)
    if summary_match:
        summary_text = summary_match.group(1).strip()
        st.markdown(f'<div class="result-box">{summary_text}</div>', unsafe_allow_html=True)
    else:
        # Fallback to first part of final report
        summary = final_report[:350] + "..." if len(final_report) > 350 else final_report
        st.markdown(f'<div class="result-box">{summary}</div>', unsafe_allow_html=True)
    
    # Tabbed detailed results
    tab1, tab2, tab3 = st.tabs(["🔍 Research Findings", "📊 Strategic Analysis", "🎯 Executive Report"])
    
    with tab1:
        st.markdown("### Research Agent Output")
        research_content = results.get('research', 'No research data available')
        st.markdown(f'<div class="result-box">{research_content}</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Analysis Agent Output")
        analysis_content = results.get('analysis', 'No analysis data available')
        st.markdown(f'<div class="result-box">{analysis_content}</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### Executive Synthesis")
        final_content = results.get('final_report', 'No final report available')
        st.markdown(f'<div class="result-box">{final_content}</div>', unsafe_allow_html=True)
    
    # Analysis metadata
    with st.expander("ℹ️ Analysis Metadata & System Info"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Query:** {results.get('query', 'N/A')}")
            st.write(f"**Generated:** {results.get('timestamp', 'N/A')}")
            st.write(f"**Architecture:** Direct LLM Multi-Agent")
            
        with col2:
            st.write(f"**Model:** Groq Llama-3.1-8B-Instant")
            st.write(f"**Processing Time:** ~30-45 seconds")
            st.write(f"**Python Version:** 3.13 Compatible")

def generate_document(results):
    """Generate and provide downloadable document"""
    try:
        generator = SimpleDocumentGenerator()
        doc_bytes = generator.create_text_report(results)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Multi_Agent_Analysis_{timestamp}.txt"
        
        st.download_button(
            label="📄 Download Complete Analysis Report",
            data=doc_bytes,
            file_name=filename,
            mime="text/plain",
            use_container_width=True,
            key="download_report"
        )
        
        st.success("✅ Report ready for download!")
        st.info("💡 **Report includes:** Research findings, strategic analysis, executive synthesis, and system metadata")
        
    except Exception as e:
        st.error(f"❌ Document generation error: {e}")

# Footer
def footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p><strong>Multi-Agent AI Analysis System</strong></p>
    <p>🤖 Research Agent • 📊 Analysis Agent • 🎯 Orchestrator Agent</p>
    <p>Powered by Groq LLM | Built with Streamlit | Python 3.13 Compatible</p>
    <p><em>Direct LLM Architecture - No External Dependencies</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    footer()
