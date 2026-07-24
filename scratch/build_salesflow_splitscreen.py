import os

html_content = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="facebook-domain-verification" content="uxu3ulx64y6d7zw7apaaeweoy090ak" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SalesFlow AI — Intelligent WhatsApp Sales Agents for Your Business | Sales Na Water</title>
    <meta name="description" content="SalesFlow AI. Automate your WhatsApp sales conversations with AI-powered agents that close deals 24/7. Sales na water! Built for Nigerian businesses that want to scale.">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        display: ['Outfit', 'sans-serif'],
                    },
                    colors: {
                        lightgreen: '#e6f4ea',
                        brandgreen: '#10b981',
                        darkgreen: '#064e3b',
                        coral: '#ff7f50',
                        offwhite: '#f8f9fa'
                    }
                }
            }
        }
    </script>
    <style>
        #demoMessages::-webkit-scrollbar { width: 4px; }
        #demoMessages::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    </style>
    <!-- Supabase JS Library -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script>
        const SUPABASE_URL = 'https://jmifkdmrybjueiipkqru.supabase.co';
        const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptaWZrZG1yeWJqdWVpaXBrcXJ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg1MjI0MDAsImV4cCI6MjA5NDA5ODQwMH0.Ft8iqBoeDzkpaxfnn7p4sxKpdq3uDy0GVW_O1LnQALk';
        const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        
        async function checkNavbarAuth() {
            try {
                const { data: { session } } = await supabaseClient.auth.getSession();
                const loggedIn = session || localStorage.getItem('supabase.auth.token') || localStorage.getItem('salesflow_user_id');
                const authLink = document.getElementById('navAuthLink');
                const ctaLink = document.getElementById('navCtaLink');
                const heroBtn = document.getElementById('heroStartBtn');
                
                if (loggedIn) {
                    if (authLink) {
                        authLink.innerText = 'Account';
                        authLink.href = 'dashboard.html';
                    }
                    if (ctaLink) {
                        ctaLink.innerText = 'Dashboard →';
                        ctaLink.href = 'dashboard.html';
                    }
                    if (heroBtn) {
                        heroBtn.innerText = 'Go to Dashboard →';
                        heroBtn.href = 'dashboard.html';
                    }
                }
            } catch (e) {
                console.error("checkNavbarAuth error:", e);
            }
        }
        document.addEventListener('DOMContentLoaded', checkNavbarAuth);
    </script>
</head>
<body class="bg-offwhite dark:bg-gray-950 text-gray-800 dark:text-gray-200 antialiased selection:bg-brandgreen selection:text-white transition-colors duration-300">

    <!-- Split Screen Hero -->
    <main class="relative min-h-screen flex flex-col lg:flex-row overflow-hidden">
        
        <!-- Left Side: Soft Off-White -->
        <div class="w-full lg:w-1/2 bg-offwhite dark:bg-gray-950 flex flex-col justify-between px-6 py-10 sm:px-12 lg:px-24 xl:px-32 z-0">
            
            <!-- Navbar -->
            <nav class="flex items-center justify-between mb-12 sm:mb-16">
                <a href="#" class="flex items-center gap-2">
                    <span class="font-display font-bold text-xl sm:text-2xl tracking-tight text-gray-900 dark:text-white">SalesFlow<span class="text-brandgreen">AI</span></span>
                </a>
                <div class="flex items-center gap-4 sm:gap-6">
                    <div class="hidden md:flex items-center gap-6 font-medium text-sm text-gray-600">
                        <a href="#features" class="hover:text-brandgreen transition-colors">Features</a>
                        <a href="#how-it-works" class="hover:text-brandgreen transition-colors">How It Works</a>
                        <a href="#pricing" class="hover:text-brandgreen transition-colors">Pricing</a>
                        <a href="login.html" id="navAuthLink" class="hover:text-brandgreen transition-colors">Login</a>
                    </div>
                    <a href="#contact" id="navCtaLink" class="inline-flex px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl bg-gray-900 text-white font-medium text-xs sm:text-sm hover:opacity-90 transition-opacity">Get Started</a>
                </div>
            </nav>

            <!-- Hero Content -->
            <div class="max-w-xl my-auto py-6 sm:py-0">
                <h1 class="font-display text-3xl sm:text-5xl lg:text-6xl xl:text-7xl font-extrabold leading-[1.15] sm:leading-[1.1] tracking-tight text-gray-900 dark:text-white mb-6">
                    Sales Na Water. <br>
                    <span class="text-brandgreen">Your AI Sales Agent</span> That Never Sleeps.
                </h1>
                <p class="text-base sm:text-lg text-gray-600 dark:text-gray-400 mb-8 sm:mb-10 leading-relaxed max-w-lg font-sans">
                    Turn your WhatsApp into a 24/7 revenue machine. Our AI agents engage leads, answer questions, handle objections, and close deals automatically.
                </p>
                <div class="flex flex-col sm:flex-row items-center gap-4">
                    <a href="#contact" id="heroStartBtn" class="w-full sm:w-auto text-center px-8 py-4 rounded-xl bg-brandgreen text-white font-semibold text-base sm:text-lg shadow-[0_8px_20px_rgba(16,185,129,0.3)] hover:shadow-[0_8px_25px_rgba(16,185,129,0.4)] hover:-translate-y-0.5 transition-all duration-300">
                        Start Free Trial
                    </a>
                    <a href="#demo" class="w-full sm:w-auto text-center px-8 py-4 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 font-semibold text-base sm:text-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                        Watch Demo
                    </a>
                </div>
            </div>

            <!-- Partner Logos -->
            <div class="mt-12 sm:mt-20 pt-6 sm:pt-8 border-t border-gray-200 dark:border-gray-800">
                <p class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-4 sm:mb-6">Trusted Infrastructure Partners</p>
                <div class="flex items-center gap-6 sm:gap-8 opacity-60 grayscale hover:grayscale-0 transition-all duration-500 flex-wrap">
                    <i class="fa-brands fa-meta text-2xl sm:text-3xl"></i>
                    <i class="fa-brands fa-google text-2xl sm:text-3xl"></i>
                    <span class="font-bold text-xl sm:text-2xl tracking-tight" style="font-family: 'Inter', sans-serif;">paystack</span>
                    <i class="fa-brands fa-aws text-2xl sm:text-3xl"></i>
                </div>
            </div>
            
        </div>

        <!-- Right Side: LIGHT GREEN Backdrop with Live Demo Card -->
        <div class="w-full lg:w-1/2 bg-lightgreen relative min-h-[420px] sm:min-h-[500px] lg:min-h-screen flex items-center justify-center p-4 sm:p-8 lg:p-12 xl:p-16">
            <!-- Decorative geometric shapes -->
            <div class="absolute top-0 right-0 w-[600px] h-[600px] bg-brandgreen opacity-10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
            
            <!-- Live Demo Chat Card (Replaces Photo) -->
            <div class="relative z-10 w-full max-w-md lg:max-w-lg bg-white rounded-2xl border border-gray-200/80 shadow-2xl overflow-hidden">
                <div class="p-3.5 sm:p-4 bg-white border-b border-gray-100 flex items-center justify-between">
                    <div class="flex items-center gap-2.5">
                        <div class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
                        <span class="font-display font-semibold text-xs sm:text-sm text-gray-900">SalesFlow AI Sandbox Demo</span>
                    </div>
                    <span class="text-[10px] sm:text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-brandgreen uppercase tracking-wider">Live</span>
                </div>
                <div id="demoMessages" class="p-4 sm:p-5 h-64 sm:h-72 lg:h-80 overflow-y-auto space-y-3 text-xs sm:text-sm font-sans bg-gray-50/50">
                    <div class="p-3 max-w-[88%] rounded-2xl rounded-tl-sm bg-white text-gray-800 shadow-sm border border-gray-100 leading-relaxed">
                        👋 Hello! I am SalesFlow AI. Ask me anything about products, pricing, or Lagos delivery!
                    </div>
                </div>
                <div class="p-2.5 sm:p-3 bg-white border-t border-gray-100 flex gap-2">
                    <input type="text" id="demoInput" placeholder="Try asking: 'How much is Jordan 4?'" class="flex-1 px-3 py-2 sm:px-4 sm:py-2.5 rounded-xl border border-gray-200 bg-gray-50 text-gray-900 text-xs sm:text-sm focus:outline-none focus:border-brandgreen min-w-0">
                    <button id="demoSend" class="px-3.5 py-2 sm:px-5 sm:py-2.5 rounded-xl bg-brandgreen text-white font-semibold text-xs sm:text-sm hover:bg-brandgreen/90 transition-colors whitespace-nowrap shrink-0">Send</button>
                </div>
            </div>

        </div>

    </main>

    <!-- Features Section -->
    <section class="py-24 bg-white dark:bg-gray-900" id="features">
        <div class="max-w-7xl mx-auto px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16">
                <span class="px-4 py-1.5 rounded-full bg-lightgreen text-brandgreen font-semibold text-xs uppercase tracking-wider">Features</span>
                <h2 class="font-display text-3xl sm:text-4xl font-extrabold text-gray-900 dark:text-white mt-4 mb-4">Everything You Need to <span class="text-brandgreen">Automate Sales</span></h2>
                <p class="text-gray-600 dark:text-gray-400 text-base">Our AI agents are built to sell, not just chat. Every feature is designed to drive revenue.</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                <div class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 hover:border-brandgreen transition-colors group">
                    <div class="w-12 h-12 rounded-xl bg-lightgreen text-brandgreen flex items-center justify-center text-xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fa-solid fa-brain"></i>
                    </div>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-3">AI-Powered Conversations</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Powered by Llama 3 & Gemini, our agents understand context, remember past chats, and respond naturally.</p>
                </div>
                <div class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 hover:border-brandgreen transition-colors group">
                    <div class="w-12 h-12 rounded-xl bg-lightgreen text-brandgreen flex items-center justify-center text-xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fa-brands fa-whatsapp"></i>
                    </div>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-3">WhatsApp Native</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Works directly on WhatsApp — the platform your customers already use. Zero friction.</p>
                </div>
                <div class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 hover:border-brandgreen transition-colors group">
                    <div class="w-12 h-12 rounded-xl bg-lightgreen text-brandgreen flex items-center justify-center text-xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fa-solid fa-bullseye"></i>
                    </div>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-3">Sales-Focused AI</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Trained in consultative selling, objection handling, and closing techniques that convert leads.</p>
                </div>
                <div class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 hover:border-brandgreen transition-colors group">
                    <div class="w-12 h-12 rounded-xl bg-lightgreen text-brandgreen flex items-center justify-center text-xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fa-solid fa-clock"></i>
                    </div>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-3">24/7 Availability</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Responds instantly at 3 AM, on weekends, and public holidays — when competitors are offline.</p>
                </div>
                <div class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 hover:border-brandgreen transition-colors group">
                    <div class="w-12 h-12 rounded-xl bg-lightgreen text-brandgreen flex items-center justify-center text-xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fa-solid fa-chart-pie"></i>
                    </div>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-3">Analytics Dashboard</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Track conversations, conversion rates, popular questions, and sales revenue generated.</p>
                </div>
                <div class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 hover:border-brandgreen transition-colors group">
                    <div class="w-12 h-12 rounded-xl bg-lightgreen text-brandgreen flex items-center justify-center text-xl mb-6 group-hover:scale-110 transition-transform">
                        <i class="fa-solid fa-sliders"></i>
                    </div>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-3">Custom Brand Voice</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">We train your AI agent to match your brand personality, tone, and specific catalog pricing.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- How It Works Section -->
    <section class="py-24 bg-offwhite dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800" id="how-it-works">
        <div class="max-w-7xl mx-auto px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16">
                <span class="px-4 py-1.5 rounded-full bg-lightgreen text-brandgreen font-semibold text-xs uppercase tracking-wider">How It Works</span>
                <h2 class="font-display text-3xl sm:text-4xl font-extrabold text-gray-900 dark:text-white mt-4 mb-4">Get Started in <span class="text-brandgreen">3 Simple Steps</span></h2>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="p-8 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
                    <span class="font-display font-black text-4xl text-brandgreen mb-4 block">01</span>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-2">Connect WhatsApp</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm">Scan a QR code to securely link your WhatsApp number in seconds.</p>
                </div>
                <div class="p-8 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
                    <span class="font-display font-black text-4xl text-brandgreen mb-4 block">02</span>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-2">Upload Catalog</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm">Add your products, FAQs, and payment details into the dashboard.</p>
                </div>
                <div class="p-8 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
                    <span class="font-display font-black text-4xl text-brandgreen mb-4 block">03</span>
                    <h3 class="font-display text-xl font-bold text-gray-900 dark:text-white mb-2">Autopilot Sales</h3>
                    <p class="text-gray-600 dark:text-gray-400 text-sm">Sit back as your AI agent chats, qualifies, and receives payments 24/7.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing Section -->
    <section class="py-24 bg-white dark:bg-gray-900" id="pricing">
        <div class="max-w-7xl mx-auto px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16">
                <span class="px-4 py-1.5 rounded-full bg-lightgreen text-brandgreen font-semibold text-xs uppercase tracking-wider">Pricing</span>
                <h2 class="font-display text-3xl sm:text-4xl font-extrabold text-gray-900 dark:text-white mt-4 mb-4">Simple, Transparent <span class="text-brandgreen">Pricing</span></h2>
                <p class="text-gray-600 dark:text-gray-400 text-base">Choose the tier that fits your sales volume. All plans include onboarding setup.</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <!-- Starter -->
                <div class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 flex flex-col justify-between">
                    <div>
                        <h3 class="font-display text-2xl font-bold text-gray-900 dark:text-white mb-2">Starter</h3>
                        <p class="text-gray-500 dark:text-gray-400 text-xs mb-6">Perfect for small merchants getting started</p>
                        <div class="mb-6">
                            <span class="text-3xl font-extrabold text-gray-900 dark:text-white">₦75,000</span>
                            <span class="text-gray-500 text-sm">/month</span>
                        </div>
                        <ul class="space-y-3 text-sm text-gray-600 dark:text-gray-400 mb-8">
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Up to 500 conversations/mo</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> 1 WhatsApp Number</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Custom AI persona setup</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Standard analytics</li>
                        </ul>
                    </div>
                    <button onclick="openPaystackCheckout('starter', 7500000)" class="w-full py-3 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-semibold text-sm hover:opacity-90 transition-opacity">⚡ Pay & Start</button>
                </div>
                <!-- Professional -->
                <div class="p-8 rounded-2xl bg-white dark:bg-gray-950 border-2 border-brandgreen relative flex flex-col justify-between shadow-xl">
                    <span class="absolute -top-3.5 right-6 px-3 py-1 rounded-full bg-brandgreen text-white font-semibold text-xs">Most Popular</span>
                    <div>
                        <h3 class="font-display text-2xl font-bold text-gray-900 dark:text-white mb-2">Professional</h3>
                        <p class="text-gray-500 dark:text-gray-400 text-xs mb-6">For growing businesses scaling sales</p>
                        <div class="mb-6">
                            <span class="text-3xl font-extrabold text-gray-900 dark:text-white">₦150,000</span>
                            <span class="text-gray-500 text-sm">/month</span>
                        </div>
                        <ul class="space-y-3 text-sm text-gray-600 dark:text-gray-400 mb-8">
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Up to 2,000 conversations/mo</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> 1 WhatsApp Number</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Advanced AI training</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Full Analytics Dashboard</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Priority Support</li>
                        </ul>
                    </div>
                    <button onclick="openPaystackCheckout('professional', 15000000)" class="w-full py-3 rounded-xl bg-brandgreen text-white font-semibold text-sm hover:bg-brandgreen/90 transition-colors shadow-md">⚡ Pay & Start</button>
                </div>
                <!-- Enterprise -->
                <div class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 flex flex-col justify-between">
                    <div>
                        <h3 class="font-display text-2xl font-bold text-gray-900 dark:text-white mb-2">Enterprise</h3>
                        <p class="text-gray-500 dark:text-gray-400 text-xs mb-6">High volume merchants & real estate</p>
                        <div class="mb-6">
                            <span class="text-3xl font-extrabold text-gray-900 dark:text-white">₦350,000</span>
                            <span class="text-gray-500 text-sm">/month</span>
                        </div>
                        <ul class="space-y-3 text-sm text-gray-600 dark:text-gray-400 mb-8">
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Unlimited conversations</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Multiple WhatsApp Numbers</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Dedicated Account Manager</li>
                            <li class="flex items-center gap-2"><i class="fa-solid fa-check text-brandgreen"></i> Custom Integrations</li>
                        </ul>
                    </div>
                    <a href="#contact" class="w-full py-3 text-center rounded-xl border border-gray-300 dark:border-gray-700 text-gray-800 dark:text-white font-semibold text-sm hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">Contact Us</a>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <section class="py-24 bg-white dark:bg-gray-900" id="contact">
        <div class="max-w-4xl mx-auto px-6">
            <div class="text-center mb-12">
                <span class="px-4 py-1.5 rounded-full bg-lightgreen text-brandgreen font-semibold text-xs uppercase tracking-wider">Contact Us</span>
                <h2 class="font-display text-3xl sm:text-4xl font-extrabold text-gray-900 dark:text-white mt-4 mb-2">Ready to Automate Your WhatsApp Sales?</h2>
                <p class="text-gray-600 dark:text-gray-400 text-sm">Fill out the form below and we will onboard your business within 24 hours.</p>
            </div>
            
            <form id="contactForm" class="p-8 rounded-2xl bg-offwhite dark:bg-gray-950 border border-gray-200 dark:border-gray-800 space-y-6">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase mb-2">Full Name</label>
                        <input type="text" id="name" required placeholder="Your name" class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-brandgreen">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase mb-2">Email Address</label>
                        <input type="email" id="email" required placeholder="you@company.com" class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-brandgreen">
                    </div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase mb-2">WhatsApp Number</label>
                        <input type="tel" id="phone" required placeholder="+234 XXX XXX XXXX" class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-brandgreen">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase mb-2">Industry</label>
                        <select id="business" required class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-brandgreen">
                            <option value="">Select Industry</option>
                            <option value="Real Estate">Real Estate</option>
                            <option value="E-Commerce">E-Commerce & Retail</option>
                            <option value="Hospitality">Hospitality & Hotels</option>
                            <option value="Services">Professional Services</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase mb-2">Message / Requirements</label>
                    <textarea id="message" rows="4" placeholder="Tell us briefly about your business..." class="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:outline-none focus:border-brandgreen"></textarea>
                </div>
                <button type="submit" class="w-full py-4 rounded-xl bg-brandgreen text-white font-semibold text-base hover:bg-brandgreen/90 transition-colors shadow-lg">Submit Request →</button>
            </form>
        </div>
    </section>

    <!-- Footer -->
    <footer class="py-12 bg-offwhite dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800">
        <div class="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div class="flex items-center gap-2">
                <span class="font-display font-bold text-xl tracking-tight text-gray-900 dark:text-white">SalesFlow<span class="text-brandgreen">AI</span></span>
                <span class="text-gray-400 text-sm">| Sales na water 🇳🇬</span>
            </div>
            <p class="text-xs text-gray-500">&copy; 2026 NEXISFLOW LTD (RC 9659504). All rights reserved.</p>
        </div>
    </footer>

    <!-- Paystack Gateway & Scripts -->
    <script src="https://js.paystack.co/v1/inline.js"></script>
    <script>
        function toggleTheme() {
            document.documentElement.classList.toggle('dark');
            const isDark = document.documentElement.classList.contains('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }

        function openPaystackCheckout(planName, amountKobo) {
            if (typeof PaystackPop === 'undefined') {
                alert('Paystack gateway loading... Please check your internet connection.');
                return;
            }
            const userEmail = localStorage.getItem('salesflow_user_email') || 'merchant@salesflowai.online';
            const businessId = localStorage.getItem('salesflow_business_id') || 'demo_merchant_001';
            
            const handler = PaystackPop.setup({
                key: 'pk_live_92208e2d32d5f2a74bc2bf9ff3a82fd32ee0fe76',
                email: userEmail,
                amount: amountKobo,
                currency: 'NGN',
                ref: 'salesflow_sub_' + Math.floor((Math.random() * 1000000000) + 1),
                metadata: {
                    custom_fields: [
                        { display_name: "Plan Type", variable_name: "plan_type", value: planName },
                        { display_name: "Business ID", variable_name: "business_id", value: businessId }
                    ]
                },
                callback: function(response) {
                    alert('🎉 Paystack Payment Successful!\nReference: ' + response.reference + '\n\nUpgrading your account tier to ' + planName.toUpperCase() + '...');
                    window.location.href = 'dashboard.html';
                },
                onClose: function() {
                    console.log('Paystack checkout closed.');
                }
            });
            handler.openIframe();
        }

        // Demo Chat Handler
        const API_BASE = 'https://api.salesaiflow.online';
        let chatHistory = [];
        const demoInput = document.getElementById('demoInput');
        const demoSend = document.getElementById('demoSend');
        const demoMessages = document.getElementById('demoMessages');

        function addMessage(text, isBot) {
            const msg = document.createElement('div');
            msg.className = `p-3 max-w-xs rounded-xl shadow-sm border ${isBot ? 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-200 dark:border-gray-700' : 'bg-brandgreen text-white ml-auto border-transparent'}`;
            msg.innerHTML = `<p>${text}</p>`;
            demoMessages.appendChild(msg);
            demoMessages.scrollTop = demoMessages.scrollHeight;
        }

        async function handleDemoSend() {
            const text = demoInput.value.trim();
            if (!text) return;

            addMessage(text, false);
            demoInput.value = '';

            chatHistory.push({ role: "user", content: text });
            if (chatHistory.length > 10) chatHistory.shift();

            const typing = document.createElement('div');
            typing.className = 'p-3 max-w-xs rounded-xl bg-white dark:bg-gray-800 text-gray-500 text-xs italic border border-gray-200 dark:border-gray-700';
            typing.innerText = 'SalesFlow AI is typing...';
            typing.id = 'typing';
            demoMessages.appendChild(typing);
            demoMessages.scrollTop = demoMessages.scrollHeight;

            try {
                const response = await fetch(`${API_BASE}/demo/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, history: chatHistory.slice(0, -1) })
                });

                const typingEl = document.getElementById('typing');
                if (typingEl) typingEl.remove();

                if (response.ok) {
                    const data = await response.json();
                    addMessage(data.reply, true);
                    chatHistory.push({ role: "assistant", content: data.reply });
                } else {
                    addMessage("Thanks for your query! We build custom AI sales bots for WhatsApp. Submit the contact form below to get started!", true);
                }
            } catch (error) {
                const typingEl = document.getElementById('typing');
                if (typingEl) typingEl.remove();
                addMessage("Thanks for your query! We build custom AI sales bots for WhatsApp. Submit the contact form below to get started!", true);
            }
        }

        if (demoSend && demoInput) {
            demoSend.addEventListener('click', handleDemoSend);
            demoInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleDemoSend(); });
        }

        // Contact Form Submission
        document.getElementById('contactForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerText = 'Sending Request...';
            btn.disabled = true;

            try {
                await fetch("https://formsubmit.co/ajax/topebayo113@gmail.com", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "Accept": "application/json" },
                    body: JSON.stringify({
                        Name: document.getElementById('name').value,
                        Email: document.getElementById('email').value,
                        Phone: document.getElementById('phone').value,
                        Industry: document.getElementById('business').value,
                        Message: document.getElementById('message').value
                    })
                });

                btn.innerText = '✓ Request Sent! We will contact you within 24h.';
                btn.style.backgroundColor = '#10b981';
                e.target.reset();
            } catch (error) {
                btn.innerText = 'Submission failed. Please try again.';
                btn.style.backgroundColor = '#ef4444';
            }

            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.style.backgroundColor = '';
                btn.disabled = false;
            }, 5000);
        });
    </script>
</body>
</html>
"""

target_path = os.path.join(os.getcwd(), "website", "index.html")
with open(target_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully generated new SalesFlow AI split-screen layout in {target_path}")
