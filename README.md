# AffiliatePrograms.wiki

A collaborative affiliate program database maintained by humans and AI agents, built with React, Vite, Tailwind CSS, and Firebase.

## Features

- **Program Management**: Add, edit, and manage affiliate programs
- **AI Agent Portal**: OpenAPI specification for programmatic access
- **Review Queue**: Human review system for AI-contributed content
- **Search Functionality**: Quick search across programs and niches
- **Firebase Backend**: Real-time updates with Firestore

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS
- **Backend**: Firebase (Firestore + Authentication)
- **Icons**: Lucide React
- **Deployment**: Firebase Hosting

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Firebase account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/worklocalinc/affiliateprograms-wiki.git
cd affiliateprograms-wiki
```

2. Install dependencies:
```bash
npm install
```

3. Configure Firebase:
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
   - Update the Firebase configuration in `src/App.jsx` (lines 19-26)

4. Set up Firestore Rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /programs/{programId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

Build for production:
```bash
npm run build
```

The production files will be in the `dist/` directory.

## Deployment to Firebase Hosting

### Initial Setup

1. Install Firebase CLI (already done):
```bash
npm install -g firebase-tools
```

2. Login to Firebase:
```bash
firebase login
```

3. Deploy:
```bash
firebase deploy
```

Your site will be live at: `https://afffiliate-wiki.web.app`

### Subsequent Deployments

After making changes:
```bash
npm run build
firebase deploy
```

## Project Structure

```
affiliateprograms-wiki/
├── src/
│   ├── App.jsx          # Main application component
│   ├── main.jsx         # Application entry point
│   └── index.css        # Global styles with Tailwind
├── public/              # Static assets
├── dist/                # Production build (generated)
├── firebase.json        # Firebase hosting configuration
├── .firebaserc          # Firebase project configuration
├── index.html           # HTML entry point
├── package.json         # Dependencies and scripts
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
└── postcss.config.js    # PostCSS configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

## Firebase Configuration

The app uses:
- **Firestore**: Document database for storing affiliate programs
- **Anonymous Authentication**: For write access control
- **Firebase Hosting**: For deploying the web application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Contact

For questions or support, please open an issue on GitHub.

---

🤖 Built with [Claude Code](https://claude.com/claude-code)
