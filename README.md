# ⚽ Match Day Poster

A real-time football match tracking application that provides live updates, automated social media posting, and interactive match predictions. Designed with a modern glassmorphism UI.

## 🚀 Features

- **Live Match Tracking**: Get real-time scores and event timelines.
- **Automated Social Media**: Automatically generate and post match event cards to Facebook.
- **Predictions**: Engage with upcoming matches by submitting your score predictions.
- **Multi-League Support**: Follow your favorite leagues (World Cup, Premier League, etc.).
- **Team Profiles**: View squad details, coach information, and team form.
- **News Feed**: Integrated news updates via RSS.

## 🛠 Tech Stack

- **Backend**: Python/Flask, Gunicorn, Gevent (for SSE).
- **Frontend**: HTML5, Modern CSS (Glassmorphism), Vanilla JavaScript.
- **Data Source**: [SportAPI](https://rapidapi.com/) (Real-time football data).
- **Deployment**: Render.

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.x
- [RapidAPI Key](https://rapidapi.com/) for [SportAPI](https://sportapi7.p.rapidapi.com/)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   RAPIDAPI_KEY=your_rapidapi_key_here
   FB_PAGE_ACCESS_TOKEN=your_facebook_token
   FB_PAGE_ID=your_facebook_page_id
   FB_PIPELINE_ENABLED=1
   ```

4. **Run the application**:
   ```bash
   python src/app.py
   ```

## 📈 Automated Updates
The application runs a background pipeline that polls the API for match events. When a goal or significant event is detected, it generates a match card and attempts to post it to the configured Facebook Page.

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements.

---
*Built with passion for the beautiful game.*
