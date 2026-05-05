"use client";

import {
  User,
  browserLocalPersistence,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  setPersistence,
  signOut as firebaseSignOut
} from "firebase/auth";
import { doc, getDoc } from "firebase/firestore";
import { createContext, useEffect, useMemo, useState } from "react";
import { firebaseAuth, firebaseDb } from "@/lib/firebase";
import { normalizeUserRole } from "@/lib/roles";
import type { UserProfile } from "@/types/auth";

type AuthContextValue = {
  firebaseUser: User | null;
  userProfile: UserProfile | null;
  profileError: string | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<UserProfile | null>;
  signOut: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

async function buildUserProfile(user: User): Promise<{
  profile: UserProfile | null;
  error: string | null;
}> {
  const userRef = doc(firebaseDb, "users", user.uid);
  const snapshot = await getDoc(userRef);

  if (!snapshot.exists()) {
    return {
      profile: null,
      error: "No se encontro documento de usuario en Firestore"
    };
  }

  const data = snapshot.data();
  const rawRole =
    typeof data.rol === "string"
      ? data.rol
      : typeof data.role === "string"
        ? data.role
        : null;

  if (!rawRole) {
    return {
      profile: null,
      error: "No se encontro rol en Firestore"
    };
  }

  const role = normalizeUserRole(rawRole);

  return {
    profile: {
      uid: user.uid,
      email: user.email,
      displayName:
        typeof data.display_name === "string"
          ? data.display_name
          : user.displayName,
      photoUrl:
        typeof data.photo_url === "string" ? data.photo_url : user.photoURL,
      role,
      rawRole
    },
    error: null
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void setPersistence(firebaseAuth, browserLocalPersistence);

    const unsubscribe = onAuthStateChanged(firebaseAuth, async (user) => {
      setLoading(true);
      setFirebaseUser(user);

      if (!user) {
        setUserProfile(null);
        setProfileError(null);
        setLoading(false);
        return;
      }

      const { profile, error } = await buildUserProfile(user);
      setUserProfile(profile);
      setProfileError(error);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      firebaseUser,
      userProfile,
      profileError,
      loading,
      signIn: async (email, password) => {
        const credentials = await signInWithEmailAndPassword(
          firebaseAuth,
          email,
          password
        );
        const { profile, error } = await buildUserProfile(credentials.user);
        setFirebaseUser(credentials.user);
        setUserProfile(profile);
        setProfileError(error);
        return profile;
      },
      signOut: async () => {
        await firebaseSignOut(firebaseAuth);
      }
    }),
    [firebaseUser, loading, profileError, userProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
