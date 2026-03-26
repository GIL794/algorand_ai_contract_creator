import streamlit as st

def inject_custom_css():
    st.markdown(
        """
        <style>
        body {
            background: #F3F5F8 !important;
            color: #1a1a1a;
        }
        .algorand-glow {
            display: block;
            margin: 0 auto 1.5rem auto;
            width: 110px;
            height: 110px;
            background: radial-gradient(circle, #00FFC2 0%, #0092D0 60%, #051D3B 100%);
            border-radius: 50%;
            box-shadow: 0 0 60px 20px #00FFC2, 0 0 120px 40px #0092D0;
            position: relative;
        }
        .algorand-glow img {
            width: 60px;
            height: 60px;
            position: absolute;
            top: 25px;
            left: 25px;
        }
        .algorand-hero {
            background: none;
            color: #00BFAE;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .algorand-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #00BFAE;
            margin-bottom: 0.5rem;
        }
        .algorand-subtitle {
            font-size: 1.2rem;
            color: #0092D0;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .algorand-desc {
            font-size: 1.05rem;
            color: #222;
            margin-bottom: 0.5rem;
        }
        .algorand-highlight {
            color: #00FFB4;
            font-weight: 700;
            margin-bottom: 1.5rem;
        }
        .algorand-cards {
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
            justify-content: center;
            margin: 2rem 0 1.5rem 0;
        }
        .algorand-card {
            background: linear-gradient(135deg, #fff 60%, #E6FFFA 100%);
            color: #051D3B;
            border-radius: 1.2rem;
            box-shadow: 0 2px 16px rgba(0,0,0,0.07);
            padding: 1.5rem 1.2rem;
            min-width: 180px;
            max-width: 240px;
            flex: 1 1 180px;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            font-size: 1.05rem;
            font-weight: 500;
            position: relative;
        }
        .algorand-card .icon {
            font-size: 1.7rem;
            margin-bottom: 0.7rem;
        }
        .algorand-section-title {
            color: #0092D0;
            font-size: 1.25rem;
            font-weight: 700;
            margin: 2.5rem 0 1.2rem 0;
            text-align: left;
        }
        .algorand-featured {
            color: #0092D0;
            font-size: 0.95rem;
            margin: 1.5rem 0 0.5rem 0;
            text-align: center;
        }
        .algorand-ecosystem-logos {
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .algorand-ecosystem-logos img {
            height: 28px;
            opacity: 0.7;
        }
        .algorand-video {
            width: 100%;
            max-width: 420px;
            border-radius: 1rem;
            margin: 1.5rem auto 2rem auto;
            display: block;
            box-shadow: 0 2px 12px rgba(0,0,0,0.10);
        }
        .algorand-testimonials {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: center;
            margin: 2rem 0 1.5rem 0;
        }
        .algorand-testimonial-box {
            background: #fff;
            color: #051D3B;
            border-radius: 0.8rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.07);
            padding: 1rem 1.2rem;
            min-width: 180px;
            max-width: 320px;
            font-size: 1rem;
            font-style: normal;
        }
        .algorand-testimonial-author {
            color: #0092D0;
            font-size: 0.95rem;
            margin-top: 0.5rem;
        }
        .algorand-cta-btn {
            background: linear-gradient(90deg, #00FFB4 0%, #0092D0 100%);
            color: #fff;
            border: none;
            border-radius: 2rem;
            padding: 1.1rem 2.5rem;
            font-size: 1.25rem;
            font-weight: 700;
            margin: 2.5rem auto 0 auto;
            display: block;
            box-shadow: 0 2px 16px rgba(0,255,180,0.13);
            cursor: pointer;
            transition: background 0.2s;
        }
        .algorand-cta-btn:hover {
            background: linear-gradient(90deg, #0092D0 0%, #00FFB4 100%);
        }
        .algorand-cta-caption {
            color: #0092D0;
            font-size: 0.98rem;
            text-align: center;
            margin-top: 0.7rem;
        }
        @media (max-width: 900px) {
            .algorand-cards, .algorand-testimonials {
                flex-direction: column;
                gap: 1.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def landing_page():

    inject_custom_css()
    st.set_page_config(
        page_title="Algorand AI Contract Creator",
        page_icon="🔗",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Glowing logo
    st.markdown(
        '''<div class="algorand-glow"><img src="https://cryptologos.cc/logos/algorand-algo-logo.png?v=026" alt="Algorand Logo" /></div>''',
        unsafe_allow_html=True,
    )
    # Hero Section
    st.markdown(
        '''<div class="algorand-hero">
            <div class="algorand-title">🚀 Algorand AI Contract Creator</div>
            <div class="algorand-subtitle">The Most Stunning Way to Build on Algorand</div>
            <div class="algorand-desc">Unleash your creativity and build the future of finance on the fastest, greenest, and most advanced Layer-1 blockchain.</div>
            <div class="algorand-highlight">100% Algorand. Pure Layer-1. Pure Innovation.</div>
        </div>''',
        unsafe_allow_html=True,
    )
    # Cards grid
    st.markdown(
        '''<div class="algorand-section-title">Why Algorand AI Contract Creator?</div>
        <div class="algorand-cards">
            <div class="algorand-card"><span class="icon">⚡</span>Lightning-fast contract generation<br><span style="color:#b0b0b0;font-size:0.95em;">No coding required</span></div>
            <div class="algorand-card"><span class="icon">🛡️</span>Security by design<br><span style="color:#b0b0b0;font-size:0.95em;">Audit-ready output</span></div>
            <div class="algorand-card"><span class="icon">💡</span>Accessible for all<br><span style="color:#b0b0b0;font-size:0.95em;">WCAG 2.1 AA+ compliant</span></div>
            <div class="algorand-card"><span class="icon">🔗</span>Algorand native<br><span style="color:#b0b0b0;font-size:0.95em;">No cross-chain confusion</span></div>
            <div class="algorand-card"><span class="icon">🌱</span>Eco-friendly blockchain<br><span style="color:#b0b0b0;font-size:0.95em;">Carbon negative</span></div>
            <div class="algorand-card"><span class="icon">🧠</span>AI-powered simplicity<br><span style="color:#b0b0b0;font-size:0.95em;">Describe, generate, deploy</span></div>
        </div>''',
        unsafe_allow_html=True,
    )
    # Featured in ecosystem (placeholder logos)
    st.markdown(
        '''<div class="algorand-featured">Featured in the Algorand Ecosystem:</div>
        <div class="algorand-ecosystem-logos">
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/6a/JavaScript-logo.png" alt="Logo1" />
            <img src="https://upload.wikimedia.org/wikipedia/commons/0/05/Go_Logo_Blue.svg" alt="Logo2" />
            <img src="https://upload.wikimedia.org/wikipedia/commons/1/1b/Python_logo_65.svg" alt="Logo3" />
        </div>''',
        unsafe_allow_html=True,
    )
    # Video (unavailable placeholder)
    st.markdown(
        '''<div style="display:flex;justify-content:center;"><div><iframe class="algorand-video" src="https://www.youtube.com/embed/invalid" title="Video unavailable" frameborder="0" allowfullscreen></iframe></div></div>''',
        unsafe_allow_html=True,
    )
    # Testimonials
    st.markdown(
        '''<div class="algorand-section-title">What Algorand Innovators Say</div>
        <div class="algorand-testimonials">
            <div class="algorand-testimonial-box">"This platform made Algorand contract development 10x faster for our team."<div class="algorand-testimonial-author">– Blockchain Startup CTO</div></div>
            <div class="algorand-testimonial-box">"The AI explanations helped me learn PyTeal and Algorand security best practices."<div class="algorand-testimonial-author">– New Algorand Developer</div></div>
            <div class="algorand-testimonial-box">"Finally, a tool that puts Algorand first. The UI is beautiful and intuitive."<div class="algorand-testimonial-author">– Ecosystem Advocate</div></div>
        </div>''',
        unsafe_allow_html=True,
    )
    # CTA Button
    st.markdown(
        '''<a href="#" style="text-decoration:none;"><button class="algorand-cta-btn">Enter the App →</button></a>
        <div class="algorand-cta-caption">Ready to build the next Algorand unicorn?</div>''',
        unsafe_allow_html=True,
    )

# Run the landing page if this file is executed directly
if __name__ == "__main__":
    landing_page()

