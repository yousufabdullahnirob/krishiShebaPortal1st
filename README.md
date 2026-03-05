# Krishisheba Portal (কৃষিসেবা পোর্টাল)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stack](https://img.shields.io/badge/Stack-Django--React-blue)](https://github.com/yousufabdullahnirob/krishiShebaPortal1st)

**Krishisheba Portal** is an AI-driven agritech platform designed to empower marginalized farmers in Bangladesh. By bridging the gap between traditional farming and modern technology, the portal provides data-backed insights, intelligent disease diagnosis, and financial management tools.

> **Concise Description**: An AI-powered agricultural service portal providing intelligent crop recommendations, disease diagnosis (Agri-Doctor), market price tracking, and financial calculators. Built with Django, React, and Scikit-learn.

---

## 🌟 Key Features

- **🌾 AI Crop Recommendation**: Uses a Random Forest Machine Learning model to suggest the most profitable crops based on soil type (`clay`, `loam`, `sandy`, `silt`), season (`kharif`, `rabi`, `zaid`), and regional data.
- **🩺 Agri-Doctor**: A dedicated problem-solving platform where farmers can upload images/videos of crop issues. It features automated AI analysis followed by expert human review and tracking IDs for every case.
- **📊 Market Price Tracking**: Real-time visibility into crop prices across different markets and districts (e.g., Dhaka, Rajshahi, Cumilla), helping farmers avoid exploitation by middlemen.
- **💰 Expense & Profit Calculator**: Integrated financial tools to calculate production costs (seeds, labor, fertilizer) and predict ROI/profit margins based on expected yield and current market prices.
- **📅 Intelligent Crop Timeline**: PERT-based activity management (Land Prep, Seed Planting, etc.) that calculates optimistic/pessimistic timelines and accounts for weather-related delays.
- **🔐 Multi-Role Access**: Dedicated dashboards for **Farmers**, **Buyers**, **Experts**, and **Admins**.
- **💬 Real-time Communication**: Integrated chat and notification system for immediate expert advice and system alerts.

---

## 🛠️ Tech Stack

### Backend

- **Framework**: Django & Django REST Framework
- **Machine Learning**: Scikit-Learn (Random Forest)
- **Database**: SQLite (Dev) / PostgreSQL (Prod)
- **Real-time**: Django Channels (WebSockets)
- **Authentication**: JWT & OTP-based verification

### Frontend

- **Framework**: React.js
- **Styling**: Tailwind CSS
- **State Management**: Context API / Redux
- **Icons**: Lucide React / FontAwesome

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Installation

1. Navigate to the backend directory:
   ```bash
   cd fullstack_app/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the server:
   ```bash
   python manage.py runserver
   ```

### Frontend Installation

1. Navigate to the frontend directory:
   ```bash
   cd fullstack_app/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

---

## 📂 Project Structure

```text
├── fullstack_app/
│   ├── backend/        # Django Project & Apps
│   │   ├── api/        # Core business logic & models
│   │   ├── ml/         # Machine Learning training scripts & models
│   │   └── market/     # Market price management
│   └── frontend/       # React Application
└── README.md           # You are here
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

_Developed with ❤️ to empower the heartbeat of Bangladesh._
