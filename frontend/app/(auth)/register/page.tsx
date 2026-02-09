"use client";

import { useState } from "react";
import Link from "next/link";
import { useRegister } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const register = useRegister();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    register.mutate({
      name,
      email,
      password,
      password_confirmation: passwordConfirmation,
    });
  };

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4 mesh-gradient">
      <Card className="w-full max-w-md shadow-xl shadow-primary/5 border-primary/10">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl gradient-primary-text">Create an account</CardTitle>
          <CardDescription>Get started with ShopAI</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="********"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password_confirmation">Confirm Password</Label>
              <Input
                id="password_confirmation"
                type="password"
                placeholder="********"
                value={passwordConfirmation}
                onChange={(e) => setPasswordConfirmation(e.target.value)}
                required
                minLength={8}
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-3 mt-5">
            <Button type="submit" variant="gradient" className="w-full rounded-full" disabled={register.isPending}>
              {register.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Account
            </Button>
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
