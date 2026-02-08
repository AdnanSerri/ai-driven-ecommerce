"use client";

import { ProfileForm } from "@/components/account/profile-form";
import { PersonalityCard } from "@/components/personality/personality-card";

export default function AccountPage() {
  return (
    <div className="space-y-6">
      <ProfileForm />
      <PersonalityCard />
    </div>
  );
}
