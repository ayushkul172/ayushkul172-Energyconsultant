import type { SpotlightProject, AdditionalProject } from '../types/index';

export const spotlightProjects: SpotlightProject[] = [
  {
    title: 'USC Agent — Upstream Contract Intelligence Platform',
    situation:
      'Upstream oil & gas teams needed to monitor 2,800+ news articles for contract intelligence — awards, bids, phase transitions — but manual scanning missed critical updates on multi-million dollar FPSO, SURF, and subsea contracts across global markets.',
    task: 'Build a production-grade AI platform with a self-learning neural network that autonomously monitors, classifies, and detects upstream contracts in real-time — with zero dependency on external APIs.',
    action:
      `🤖 INTELLIGENT ARTICLE CLASSIFICATION
• Review articles one-by-one with full context, agent guidance, and AI predictions
• Classify as Important / Unimportant / Doubt / ProjectFlow / Noted / Follow-up
• Forward/backward navigation with skip functionality
• Auto-saves classifications to Excel with color coding

🧠 SELF-LEARNING NEURAL NETWORK
• PyTorch classifier (3.65M parameters) trained on your classification decisions
• TF-IDF tokenization with 28,499 features (unlimited vocabulary)
• Configurable architecture — adjust layers, neurons, dropout, learning rate from the UI
• Live visualization of network architecture, training loss, feature importance
• Auto-retrains every 5 new classifications (Model v130, 6700 epochs, 100% accuracy)

📋 HYBRID CONTRACT DETECTION ENGINE
• Regex pattern engine — detects awards, bids/tenders, signings, phase transitions
• Priority scorer (0-100) based on build parts, contract stages, actions, budget, recency
• Milestone filtering — distinguishes real tenders from project approvals
• Event deduplication and urgency scoring (1-10)

🔔 AUTONOMOUS BACKGROUND AGENT
• Runs 24/7, analyzes untouched articles every 60 minutes
• Auto-classifies high-confidence articles (green/orange)
• Pops up desktop notifications for articles requiring human attention
• Learns from your decisions to improve over time

💬 SMART LOCAL AI ANALYSIS (No API needed)
• Automatic article analysis on load — priority, contracts, companies, values
• Extractive summarization using TextRank sentence scoring
• Company role detection (operator, contractor, partner)
• Domain-specific key term detection (80+ upstream O&G terms)
• Interactive Q&A: "is this important?", "summarize", "companies", "contracts"

📊 WEB DASHBOARD (Flask + SocketIO)
• Real-time stats: total articles, touched, untouched, % complete
• Contract alerts panel with confirm/dismiss/snooze
• Brain learning metrics (decisions, companies tracked, accuracy)
• Full data table with pagination and status filtering

🏗️ DOMAIN KNOWLEDGE
Build Parts: FPSO, FLNG, FSRU, SURF, Topsides, Hull, Jacket, Pipeline, Subsea, Manifold, Wellhead, Riser, Umbilical
Contract Stages: EPC, EPCI, FEED, Pre-FEED, FID, LOA, ITT, Installation, Hook-up, O&M, Decommissioning
Contract Actions: awarded, won, secured, signed, selected, shortlisted, sanctioned

⚙️ ARCHITECTURE
Web Dashboard (Flask + SocketIO + Real-time Updates) → Application Layer (Article Service | Classification | Alert Manager) → Intelligence Layer (Contract Engine [Regex + ML] | ML Brain [PyTorch] | Priority Scorer [Domain Rules]) → Data Layer (Excel Sync | Brain Memory | ML Model Files) → Autonomous Agent (Scan → Analyze → Classify → Alert)

🧪 ML MODEL DETAILS
• Architecture: Input (TF-IDF 28,499) → Dense(128) + ReLU + Dropout(0.3) → Dense(64) + ReLU + Dropout(0.2) → Output(6) → Softmax
• Training Data: 552 classified articles
• Parameters: 3,656,386
• Training Accuracy: 100%
• Auto-retraining: Every 5 new classifications`,
    techStack: ['PyTorch', 'Flask', 'SocketIO', 'spaCy', 'TF-IDF', 'scikit-learn', 'APScheduler', 'pandas'],
    image: 'https://raw.githubusercontent.com/ayushkul172/ayushkul172-Energyconsultant/main/AI%20tool%20analysis.jpg',
    results: [
      { metric: '3.65M', description: 'PyTorch neural network parameters with self-learning capability.' },
      { metric: '100%', description: 'Training accuracy — 552 samples, 6700 epochs, model v130.' },
      { metric: '2812', description: 'Articles processed — 77.2% auto-classified by autonomous agent.' },
    ],
    accentColor: 'from-cyan-500 to-blue-600',
  },
  {
    title: 'Offshore Drilling Intelligence Platform',
    situation:
      'Oil & gas operators lacked integrated intelligence systems for rig efficiency analysis, climate risk assessment, and contractor evaluation — leading to $2-5M cost overruns per project and 8+ hours spent on manual contractor evaluations.',
    task: 'Build an enterprise-grade analytics platform with 15+ AI modules covering climate intelligence, rig-well matching, Monte Carlo risk simulation, NLP chatbot, and real-time dashboards for offshore drilling decision-making.',
    action:
      `Built a full-stack Streamlit application (7,000+ lines of Python) with:
• Climate intelligence engine covering 30+ global regions
• ML-based rig-well matching algorithm achieving 95% accuracy
• Monte Carlo simulators for project risk quantification and cost modeling
• NLP chatbot for natural language data queries across drilling databases
• Real-time efficiency scoring with anomaly detection for fleet monitoring
• 50+ interactive dashboards for contract negotiations and benchmarking
• Contractor evaluation scoring system with historical performance analysis`,
    techStack: ['Python', 'Streamlit', 'scikit-learn', 'Monte Carlo', 'NLP', 'Pandas', 'Plotly'],
    image: 'https://images.unsplash.com/photo-1518709766631-a6a7f45921c3?q=80&w=1200&h=800&fit=crop&auto=format',
    results: [
      { metric: '15+', description: 'AI modules for drilling intelligence and risk analysis.' },
      { metric: '95%', description: 'Rig-well matching accuracy with ML algorithm.' },
      { metric: '8hrs→15min', description: 'Contractor evaluation time reduction.' },
    ],
    accentColor: 'from-indigo-500 to-purple-600',
  },
  {
    title: 'Upstream AI Analyzer Tool',
    situation:
      'In the upstream oil & gas industry, decision-makers rely on timely insights from news sources. However, manually scanning, extracting, and analyzing key information is tedious, error-prone, and time-consuming, leading to missed updates and difficulties in building structured dashboards.',
    task: 'Design and build a tool that could automatically collect upstream news, extract specific entities (projects, operators, delays), summarize articles, and visually present the analysis in an interactive dashboard—all accessible to non-technical users.',
    action:
      'Built the Upstream AI Analyzer, a full-featured Python desktop application. The tool\'s workflow involves a user selecting a date range, which triggers automated web scraping of news articles. Each article is processed through a custom NLP extraction pipeline to pull over 14 categories of information, including field names, companies, contract types, and budget values. The structured results are rendered in a dynamic, graphical dashboard.',
    techStack: ['PyQt5', 'Selenium', 'spaCy', 'Regex', 'Matplotlib', 'Python'],
    image: 'https://raw.githubusercontent.com/ayushkul172/ayushkul172-Energyconsultant/main/AI%20tool%20analysis.jpg',
    results: [
      { metric: '90%', description: 'Reduction in manual analysis time for upstream analysts.' },
      { metric: '100%', description: 'Automation of intelligence gathering from unstructured news.' },
      { metric: '1-Click', description: 'Deployment, launched from a single desktop icon for non-technical users.' },
    ],
    accentColor: 'from-cyan-500 to-blue-600',
  },
  {
    title: 'Upstream AI Data Matcher Tool',
    situation:
      'In the upstream oil & gas industry, reconciling data from multiple sources is critical for accurate decision-making, but manual matching is slow, error-prone, and leads to inconsistencies across datasets.',
    task: 'Design an automated data matching tool that utilizes AI to enhance accuracy, streamlines the reconciliation process, and provides a user-friendly, interactive dashboard for non-technical users.',
    action:
      'Built the Upstream Data Matcher, a Python desktop application that combines multiple data matching algorithms (fuzzy, semantic, cosine similarity) with AI-powered features. The tool uses NLP and machine learning to intelligently analyze and compare datasets, automatically identifies matches, improves accuracy with user feedback, and allows users to train a Random Forest model to enhance future predictions.',
    techStack: ['tkinter', 'pandas', 'fuzzywuzzy', 'spaCy', 'sklearn', 'threading'],
    image: 'https://raw.githubusercontent.com/ayushkul172/ayushkul172-Energyconsultant/main/AI%20matching%20tool.png',
    results: [
      { metric: '95%', description: 'Improvement in data matching accuracy with AI-powered algorithms.' },
      { metric: '80%', description: 'Reduction in manual data reconciliation time for upstream teams.' },
      { metric: '1-Click', description: 'Seamless deployment and user access via a simple desktop interface.' },
    ],
    accentColor: 'from-purple-500 to-indigo-600',
  },
  {
    title: 'Automated Research Synthesizer',
    situation:
      'Strategic research teams were bogged down by manual data collection from diverse online sources. This time-consuming process led to project delays and made it difficult to synthesize information into a consistent, actionable format.',
    task: 'Create an intelligent tool that leverages Generative AI to automate the entire secondary research lifecycle—from targeted data gathering and summarization to the final synthesis of key insights, freeing up analysts for higher-value strategic thinking.',
    action:
      'Engineered a Python-based application that integrates with the OpenAI API. An analyst provides a research query, and the tool autonomously scours predefined industry websites and news outlets. It uses BeautifulSoup for content extraction and LangChain to structure prompts for summarization, theme identification, and insight generation. The final, synthesized report is automatically compiled into a structured Word document.',
    techStack: ['Python', 'OpenAI API', 'LangChain', 'BeautifulSoup', 'python-docx'],
    image: 'https://images.unsplash.com/photo-1677756119517-756a188d2d94?q=80&w=1200&h=800&fit=crop&auto=format',
    results: [
      { metric: '75%', description: 'Reduction in time spent on initial data gathering and synthesis.' },
      { metric: '4x', description: 'Increase in the volume of sources analyzed per research project.' },
      { metric: '100%', description: 'Standardization of research outputs for improved consistency.' },
    ],
    accentColor: 'from-green-500 to-teal-600',
  },
  {
    title: 'Project Command Center',
    situation:
      'Managing complex projects with multiple team members often leads to fragmented data, unbalanced workloads, and a lack of real-time visibility. Traditional tools struggle to provide intelligent insights, forcing managers into manual tracking and reactive decision-making.',
    task: 'Design and develop an all-in-one desktop application that centralizes project management, provides granular sub-task tracking, and integrates AI-powered analytics to predict delays, summarize workloads, and intelligently optimize task allocation across the team.',
    action:
      "Developed the 'Project Command Center,' a comprehensive solution featuring a dynamic task table with Excel integration. Key innovations include an AI-powered observation module using NLP to summarize workloads, a machine learning model to predict task completion, and a linear programming engine to optimize resource allocation. The platform includes an interactive visualization panel with customizable charts and advanced filtering.",
    techStack: ['Python', 'PyQt5', 'Pandas', 'Scikit-learn', 'Matplotlib', 'SciPy'],
    image: 'https://raw.githubusercontent.com/ayushkul172/ayushkul172-Energyconsultant/main/Project%20tool.png',
    results: [
      { metric: 'AI-Driven', description: 'Insights that predict delays & optimize team workload allocation.' },
      { metric: '100%', description: 'Centralized visibility into all tasks and sub-tasks in real-time.' },
      { metric: '30%+', description: 'Increase in team productivity via automation & balanced workloads.' },
    ],
    accentColor: 'from-orange-500 to-red-600',
  },
];

export const additionalProjects: AdditionalProject[] = [
  {
    title: 'AI-Powered News Intelligence Pipeline',
    challenge:
      'The upstream analysis team spent 12 hours weekly on manual news gathering, causing delays and inconsistent outputs.',
    action:
      'Architected a fully automated Python pipeline using Selenium and BeautifulSoup for web scraping, and an AI summarization engine with Newspaper3k and spaCy to generate concise briefs. The process was integrated with Microsoft Copilot for seamless delivery.',
    result: {
      text: 'in processing time, 100% data coverage with consistent formatting, and delivery of near-real-time intelligence that accelerated strategic decision-making.',
      highlight: '90% reduction',
    },
  },
  {
    title: 'Generative AI for Accelerated Secondary Research',
    challenge:
      "KPMG's ENR team was hampered by time-consuming and inefficient manual data gathering for research projects.",
    action:
      "Developed a custom solution by integrating a Generative AI tool directly into the team's workflow. Created a powerful Excel VBA macro that acted as a bridge, allowing analysts to automate a significant portion of their data gathering and synthesis tasks.",
    result: {
      text: 'Delivered a marked reduction in research time, significantly enhancing data accuracy, and creating a more efficient and scalable research process.',
      highlight: 'Game-changer',
    },
  },
];
