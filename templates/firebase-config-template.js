// Firebase configuration template
// Replace these placeholder values with your actual Firebase project configuration
const firebaseConfig = {
  apiKey: "AIzaSyD1SjKkfNFiHv4PB5lyJFyQCv1_km_WmuU",
  authDomain: "fraud-detection-app-8ae4f.firebaseapp.com",
  projectId: "fraud-detection-app-8ae4f",
  storageBucket: "fraud-detection-app-8ae4f.firebasestorage.app",
  messagingSenderId: "300143961450",
  appId: "1:300143961450:web:b160f161da105a1cb13113"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize services and make them globally available
const auth = firebase.auth();
const db = firebase.firestore();

console.log('Firebase initialized successfully');
console.log('Auth object:', auth);
console.log('Firestore object:', db);
