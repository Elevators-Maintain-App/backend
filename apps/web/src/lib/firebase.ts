import { getApp, getApps, initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const requiredFirebaseEnv = {
  NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN:
    process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET:
    process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID:
    process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  NEXT_PUBLIC_FIREBASE_APP_ID: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

function getRequiredFirebaseConfig() {
  const missingVariables = Object.entries(requiredFirebaseEnv)
    .filter(([, value]) => !value)
    .map(([key]) => key);

  if (missingVariables.length > 0) {
    throw new Error(
      [
        "VertiOne Web Firebase configuration is incomplete.",
        `Missing environment variables: ${missingVariables.join(", ")}.`,
        "Create apps/web/.env.local from apps/web/.env.example and restart the Next.js dev server."
      ].join(" ")
    );
  }

  return {
    apiKey: requiredFirebaseEnv.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: requiredFirebaseEnv.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: requiredFirebaseEnv.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: requiredFirebaseEnv.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId:
      requiredFirebaseEnv.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: requiredFirebaseEnv.NEXT_PUBLIC_FIREBASE_APP_ID
  };
}

const app = getApps().length ? getApp() : initializeApp(getRequiredFirebaseConfig());

export const firebaseAuth = getAuth(app);
export const firebaseDb = getFirestore(app);
