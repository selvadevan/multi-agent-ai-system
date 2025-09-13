# ================================
# STREAMLIT WEB UI FOR MULTI-AGENT SYSTEM
# ================================
# Hostable on Streamlit Community Cloud (FREE)
# Interactive web interface for your CrewAI multi-agent analysis
# ================================

import streamlit as st
import os
import time
from datetime import datetime
import json
import io
import base64

# Import your multi-agent system components
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

# DOCX Libraries
try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Page Configuration
st.set_page_config(
    page_title="Multi-Agent AI Analysis System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

# Document Formatter Class for Web
class WebDocumentFormatter:
    def __init__(self):
        if DOCX_AVAILABLE:
            self.document = Document()
            self.setup_styles()
    
    def setup_styles(self):
        if not DOCX_AVAILABLE:
            return
        try:
            # Setup document styles
            title_style = self.document.styles.add_style('Custom Title', WD_STYLE_TYPE.PARAGRAPH)
            title_font = title_style.font
            title_font.name = 'Calibri'
            title_font.size = Pt(20)
            title_font.bold = True
        except Exception as e:
            pass
    
    def create_document(self, results):
        if not DOCX_AVAILABLE:
            return None
            
        try:
            # Add title
            title = self.document.add_paragraph()
            title_run = title.add_run("MULTI-AGENT ANALYSIS REPORT")
            title_run.bold = True
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add content
            self.document.add_paragraph(f"Query: {results['query']}")
            self.document.add_paragraph(f"Generated: {results['timestamp']}")
            self.document.add_paragraph()
            
            # Research section
            self.document.add_paragraph().add_run("RESEARCH FINDINGS").bold = True
            self.document.add_paragraph(str(results['research']))
            self.document.add_paragraph()
            
            # Analysis section
            self.document.add_paragraph().add_run("COMPREHENSIVE ANALYSIS").bold = True
            self.document.add_paragraph(str(results['analysis']))
            self.document.add_paragraph()
            
            # Final report
            self.document.add_paragraph().add_run("EXECUTIVE SYNTHESIS").bold = True
            self.document.add_paragraph(str(results['final_report']))
            
            # Save to bytes
            doc_buffer = io.BytesIO()
            self.document.save(doc_buffer)
            doc_buffer.seek(0)
            return doc_buffer.getvalue()
            
        except Exception as e:
            st.error(f"Document generation error: {e}")
            return None

# Multi-Agent System Classes
class MultiAgentSystem:
    def __init__(self, api_key):
        self.groq_llm = LLM(
            model="groq/llama-3.1-8b-instant",
            api_key=api_key,
            max_tokens=1000,
            temperature=0.1
        )
        self.setup_agents()
    
    def setup_agents(self):
        # Research Agent
        self.research_agent = Agent(
            role='Senior Research Specialist',
            goal='Conduct comprehensive research using available knowledge',
            backstory="""Expert researcher with vast knowledge across domains.
            Excels at analyzing questions and providing comprehensive information.""",
            verbose=False,
            allow_delegation=False,
            llm=self.groq_llm,
            max_iter=2,
            max_rpm=8
        )
        
        # Analysis Agent
        self.analysis_agent = Agent(
            role='Senior Data Analyst and Strategic Advisor',
            goal='Perform comprehensive analysis and provide actionable insights',
            backstory="""World-class analyst with expertise in statistical analysis,
            pattern recognition, financial analysis, and strategic thinking.""",
            verbose=False,
            allow_delegation=False,
            llm=self.groq_llm,
            max_iter=2,
            max_rpm=8
        )
        
        # Orchestrator Agent
        self.orchestrator_agent = Agent(
            role='Chief Orchestrator and Synthesis Expert',
            goal='Coordinate workflows and synthesize executive-level reports',
            backstory="""Master coordinator and executive advisor who excels at
            managing complex analyses and creating executive-level reports.""",
            verbose=False,
            allow_delegation=False,
            llm=self.groq_llm,
            max_iter=2,
            max_rpm=8
        )
    
    def create_tasks(self, user_query, research_results=None, analysis_results=None):
        # Research Task
        research_task = Task(
            description=f"""
            Research and analyze: "{user_query}"
            
            Provide structured findings with:
            1. Key facts and current information
            2. Important statistics and data points
            3. Multiple perspectives and viewpoints
            4. Current trends and developments
            
            Keep response focused and well-structured.
            """,
            agent=self.research_agent,
            expected_output="Structured research report with key findings and context"
        )
        
        # Analysis Task
        analysis_context = f"\n\nResearch Context:\n{research_results}" if research_results else ""
        analysis_task = Task(
            description=f"""
            Analyze: "{user_query}"{analysis_context}
            
            Provide analysis covering:
            1. Quantitative insights and metrics
            2. Strategic implications and opportunities
            3. Risk assessment and considerations
            4. Predictive analysis and forecasting
            5. Strategic recommendations (3-5 priority actions)
            
            Structure with clear sections for professional presentation.
            """,
            agent=self.analysis_agent,
            expected_output="Comprehensive analysis with insights and strategic recommendations"
        )
        
        # Orchestration Task
        orchestration_context = f"""
        RESEARCH DATA: {research_results}
        ANALYSIS DATA: {analysis_results}
        """ if research_results and analysis_results else ""
        
        orchestration_task = Task(
            description=f"""
            Create executive synthesis for: "{user_query}"
            
            {orchestration_context}
            
            Create comprehensive report with:
            1. EXECUTIVE SUMMARY (3-4 key sentences)
            2. KEY FINDINGS (5 most important insights)
            3. STRATEGIC RECOMMENDATIONS (3 top priorities)
            4. IMPLEMENTATION ROADMAP (specific next steps)
            5. RISK CONSIDERATIONS (key concerns)
            6. CONCLUSION (final assessment)
            """,
            agent=self.orchestrator_agent,
            expected_output="Executive-level comprehensive report with structured recommendations"
        )
        
        return research_task, analysis_task, orchestration_task
    
    def run_analysis(self, user_query, progress_callback=None):
        """Run the complete multi-agent analysis with progress updates"""
        results = {
            'query': user_query,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Phase 1: Research
            if progress_callback:
                progress_callback("🔍 Research Agent working...", 25)
            
            research_task, _, _ = self.create_tasks(user_query)
            research_crew = Crew(
                agents=[self.research_agent],
                tasks=[research_task],
                process=Process.sequential,
                verbose=False,
                max_rpm=8
            )
            
            research_results = research_crew.kickoff()
            results['research'] = research_results
            
            # Rate limiting
            time.sleep(8)
            
            # Phase 2: Analysis
            if progress_callback:
                progress_callback("📊 Analysis Agent working...", 50)
            
            _, analysis_task, _ = self.create_tasks(user_query, str(research_results))
            analysis_crew = Crew(
                agents=[self.analysis_agent],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=False,
                max_rpm=8
            )
            
            analysis_results = analysis_crew.kickoff()
            results['analysis'] = analysis_results
            
            # Rate limiting
            time.sleep(8)
            
            # Phase 3: Orchestration
            if progress_callback:
                progress_callback("🎯 Orchestrator Agent synthesizing...", 75)
            
            _, _, orchestration_task = self.create_tasks(user_query, str(research_results), str(analysis_results))
            orchestration_crew = Crew(
                agents=[self.orchestrator_agent],
                tasks=[orchestration_task],
                process=Process.sequential,
                verbose=False,
                max_rpm=8
            )
            
            final_results = orchestration_crew.kickoff()
            results['final_report'] = final_results
            
            if progress_callback:
                progress_callback("✅ Analysis Complete!", 100)
            
            return results
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}", 0)
            return {'error': str(e)}

# Main Application
def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Multi-Agent AI Analysis System</h1>', unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key Input
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Enter your Groq API key to use the system"
        )
        
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ Please enter your Groq API key")
        
        st.markdown("---")
        
        # System Information
        st.header("🤖 Agent System")
        st.markdown("""
        <div class="agent-card">
        <h4>🔍 Research Agent</h4>
        <p>Conducts comprehensive research and information gathering</p>
        </div>
        
        <div class="agent-card">
        <h4>📊 Analysis Agent</h4>
        <p>Performs multi-dimensional analysis and strategic insights</p>
        </div>
        
        <div class="agent-card">
        <h4>🎯 Orchestrator Agent</h4>
        <p>Synthesizes results into executive-level reports</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main Interface
    if not api_key:
        st.info("👈 Please configure your Groq API key in the sidebar to get started")
        st.markdown("""
        ### Welcome to the Multi-Agent AI Analysis System
        
        This system uses three specialized AI agents to provide comprehensive analysis:
        
        1. **Research Agent** - Gathers comprehensive information
        2. **Analysis Agent** - Performs detailed analysis with insights
        3. **Orchestrator Agent** - Creates executive-level synthesis
        
        **Features:**
        - 🔍 Comprehensive multi-perspective research
        - 📊 Statistical and strategic analysis
        - 🎯 Executive-level recommendations
        - 📄 Professional document export
        - ⚡ Rate-limited for stability
        
        **To get started:**
        1. Get a free Groq API key at [console.groq.com](https://console.groq.com)
        2. Enter your API key in the sidebar
        3. Ask any question for comprehensive AI analysis
        """)
        return
    
    # Query Input
    st.header("📝 Analysis Query")
    user_query = st.text_area(
        "Enter your question for comprehensive multi-agent analysis:",
        placeholder="Example: What are the key investment opportunities in renewable energy for 2025?",
        height=100
    )
    
    # Analysis Controls
    col1, col2 = st.columns([1, 1])
    with col1:
        run_analysis = st.button("🚀 Run Multi-Agent Analysis", type="primary", use_container_width=True)
    with col2:
        if st.session_state.analysis_complete:
            generate_doc = st.button("📄 Generate Word Document", use_container_width=True)
        else:
            generate_doc = False
    
    # Progress and Results Section
    if run_analysis and user_query.strip():
        if not api_key:
            st.error("❌ Please configure your Groq API key first")
            return
        
        # Initialize system
        try:
            system = MultiAgentSystem(api_key)
        except Exception as e:
            st.error(f"❌ System initialization failed: {e}")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(message, percent):
            progress_bar.progress(percent)
            status_text.markdown(f'<p class="progress-text">{message}</p>', unsafe_allow_html=True)
        
        # Run analysis
        with st.spinner("Initializing multi-agent analysis..."):
            results = system.run_analysis(user_query, update_progress)
        
        if 'error' in results:
            st.error(f"❌ Analysis failed: {results['error']}")
            if "rate_limit" in results['error'].lower():
                st.info("💡 Rate limit reached. Please wait 60 seconds and try again.")
        else:
            st.session_state.results = results
            st.session_state.analysis_complete = True
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            display_results(results)
    
    elif st.session_state.analysis_complete and st.session_state.results:
        # Display cached results
        display_results(st.session_state.results)
    
    # Document Generation
    if generate_doc and st.session_state.results:
        generate_document(st.session_state.results)

def display_results(results):
    """Display analysis results in a structured format"""
    st.header("📋 Analysis Results")
    
    # Executive Summary
    st.subheader("🎯 Executive Summary")
    final_report = str(results.get('final_report', ''))
    if 'EXECUTIVE SUMMARY' in final_report.upper():
        summary_start = final_report.upper().find('EXECUTIVE SUMMARY')
        summary_section = final_report[summary_start:summary_start+500]
        lines = summary_section.split('\n')
        summary = ' '.join([line.strip() for line in lines[1:4] if line.strip()])
        st.markdown(f'<div class="result-box">{summary}</div>', unsafe_allow_html=True)
    
    # Tabbed Results
    tab1, tab2, tab3 = st.tabs(["🔍 Research Findings", "📊 Analysis & Insights", "🎯 Executive Report"])
    
    with tab1:
        st.markdown("### Research Agent Output")
        st.markdown(f'<div class="result-box">{results.get("research", "No research data available")}</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Analysis Agent Output")
        st.markdown(f'<div class="result-box">{results.get("analysis", "No analysis data available")}</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### Orchestrator Agent Output")
        st.markdown(f'<div class="result-box">{results.get("final_report", "No final report available")}</div>', unsafe_allow_html=True)
    
    # Metadata
    with st.expander("ℹ️ Analysis Metadata"):
        st.write(f"**Query:** {results.get('query', 'N/A')}")
        st.write(f"**Generated:** {results.get('timestamp', 'N/A')}")
        st.write(f"**System:** Hybrid Multi-Agent (CrewAI + Groq)")
        st.write(f"**Processing Time:** ~3-4 minutes")

def generate_document(results):
    """Generate and provide download for Word document"""
    if not DOCX_AVAILABLE:
        st.error("❌ Word document generation not available. python-docx library required.")
        return
    
    try:
        formatter = WebDocumentFormatter()
        doc_bytes = formatter.create_document(results)
        
        if doc_bytes:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Multi_Agent_Analysis_{timestamp}.docx"
            
            st.download_button(
                label="📄 Download Word Document",
                data=doc_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            st.success("✅ Document ready for download!")
        else:
            st.error("❌ Failed to generate document")
            
    except Exception as e:
        st.error(f"❌ Document generation error: {e}")

# Footer
def footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>Multi-Agent AI Analysis System | Powered by CrewAI + Groq | Built with Streamlit</p>
    <p>🤖 Research • 📊 Analysis • 🎯 Synthesis</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    footer()
