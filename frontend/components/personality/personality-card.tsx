"use client";

import { usePersonalityProfile, usePersonalityTraits, useRefreshPersonality } from "@/hooks/use-recommendations";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Brain, TrendingUp, ShoppingBag, Sparkles, Info, Database, Target, RefreshCw } from "lucide-react";

const PERSONALITY_LABELS: Record<string, { label: string; description: string }> = {
  adventurous_premium: {
    label: "Adventurous Premium",
    description: "You love exploring new and premium products, making quick decisions with confidence.",
  },
  cautious_value_seeker: {
    label: "Cautious Value Seeker",
    description: "You carefully evaluate products for the best value, prioritizing quality ratings and deals.",
  },
  loyal_enthusiast: {
    label: "Loyal Enthusiast",
    description: "You stick with brands you trust and engage deeply with your favorite products.",
  },
  bargain_hunter: {
    label: "Bargain Hunter",
    description: "You're always on the lookout for the best deals and discounts.",
  },
  quality_focused: {
    label: "Quality Focused",
    description: "Quality matters most to you - you thoroughly research before purchasing.",
  },
  trend_follower: {
    label: "Trend Follower",
    description: "You stay ahead of the curve, often among the first to try what's popular.",
  },
  practical_shopper: {
    label: "Practical Shopper",
    description: "You take a balanced approach, weighing value, quality, and practicality.",
  },
  impulse_buyer: {
    label: "Impulse Buyer",
    description: "You're spontaneous and excited by new arrivals and limited-time offers.",
  },
};

function getConfidenceLabel(confidence: number): { label: string; color: string } {
  if (confidence >= 0.8) return { label: "High confidence", color: "text-green-600" };
  if (confidence >= 0.5) return { label: "Moderate confidence", color: "text-yellow-600" };
  return { label: "Building profile", color: "text-muted-foreground" };
}

function getDataQualityLabel(dataPoints: number): string {
  if (dataPoints >= 50) return "Comprehensive data";
  if (dataPoints >= 20) return "Good amount of data";
  if (dataPoints >= 10) return "Growing data";
  return "Limited data";
}

export function PersonalityCard() {
  const { data: profile, isLoading: profileLoading } = usePersonalityProfile();
  const { data: traits, isLoading: traitsLoading } = usePersonalityTraits();
  const refreshMutation = useRefreshPersonality();

  const isLoading = profileLoading || traitsLoading;
  const isRefreshing = refreshMutation.isPending;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!profile) return null;

  const personalityInfo = PERSONALITY_LABELS[profile.personality_type] || {
    label: profile.personality_type?.replace(/_/g, " ") || "Unknown",
    description: "Your shopping personality is being analyzed.",
  };

  const confidenceInfo = getConfidenceLabel(profile.confidence || 0);
  const dataQualityLabel = getDataQualityLabel(profile.data_points || 0);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          Your Shopping Personality
        </CardTitle>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => refreshMutation.mutate()}
          disabled={isRefreshing}
          title="Refresh profile"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main personality type */}
        <div className="space-y-3">
          <div className="flex items-center gap-3 flex-wrap">
            <Badge variant="default" className="text-sm px-3 py-1.5">
              {personalityInfo.label}
            </Badge>
            <span className={`text-xs ${confidenceInfo.color}`}>
              {Math.round((profile.confidence || 0) * 100)}% {confidenceInfo.label}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            {personalityInfo.description}
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Database className="h-3 w-3" />
            <span>Based on {profile.data_points || 0} interactions ({dataQualityLabel})</span>
          </div>
        </div>

        {/* Trait characteristics */}
        {traits?.traits && traits.traits.length > 0 && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Your Shopping Traits
              </h4>
              <ul className="space-y-2">
                {traits.traits.map((trait, index) => (
                  <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>{trait}</span>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

        {/* Dimension breakdown */}
        {traits?.dimensions && traits.dimensions.length > 0 && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Trait Breakdown
              </h4>
              <div className="space-y-4">
                {traits.dimensions.map((dimension) => (
                  <div key={dimension.name} className="space-y-1.5">
                    <div className="flex justify-between text-sm">
                      <span className="capitalize font-medium">
                        {dimension.name.replace(/_/g, " ")}
                      </span>
                      <span className="text-muted-foreground">
                        {Math.round(dimension.score * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all"
                        style={{ width: `${Math.round(dimension.score * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {dimension.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Recommendation impact */}
        {traits?.recommendations_impact && Object.keys(traits.recommendations_impact).length > 0 && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Target className="h-4 w-4" />
                How This Affects Your Recommendations
              </h4>
              <div className="space-y-3 text-sm">
                {traits.recommendations_impact.product_selection && (
                  <div className="flex items-start gap-2">
                    <ShoppingBag className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div>
                      <span className="font-medium">Products: </span>
                      <span className="text-muted-foreground">
                        {traits.recommendations_impact.product_selection}
                      </span>
                    </div>
                  </div>
                )}
                {traits.recommendations_impact.pricing && (
                  <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div>
                      <span className="font-medium">Pricing: </span>
                      <span className="text-muted-foreground">
                        {traits.recommendations_impact.pricing}
                      </span>
                    </div>
                  </div>
                )}
                {traits.recommendations_impact.categories && (
                  <div className="flex items-start gap-2">
                    <Sparkles className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div>
                      <span className="font-medium">Categories: </span>
                      <span className="text-muted-foreground">
                        {traits.recommendations_impact.categories}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* Last updated */}
        <p className="text-xs text-muted-foreground pt-2">
          Last updated: {new Date(profile.last_updated).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  );
}
