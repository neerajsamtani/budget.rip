import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import React from "react";
import CategoriesSettings from "../components/settings/CategoriesSettings";
import EventHintsSettings from "../components/settings/EventHintsSettings";
import { PageContainer, PageHeader } from "../components/ui/layout";
import { Body, H1 } from "../components/ui/typography";

export default function SettingsPage() {
    return (
        <PageContainer>
            <PageHeader>
                <H1>Settings</H1>
                <Body className="text-muted-foreground">
                    Configure categories and event hints for your budget tracking.
                </Body>
            </PageHeader>

            <Tabs defaultValue="categories" className="space-y-6">
                <TabsList>
                    <TabsTrigger value="categories">Categories</TabsTrigger>
                    <TabsTrigger value="event-hints">Event Hints</TabsTrigger>
                </TabsList>

                <TabsContent value="categories" className="space-y-4">
                    <div className="text-sm text-muted-foreground mb-4">
                        Manage expense categories for organizing your events.
                    </div>
                    <CategoriesSettings />
                </TabsContent>

                <TabsContent value="event-hints" className="space-y-4">
                    <div className="text-sm text-muted-foreground mb-4">
                        Configure rules to automatically prefill event details when creating events from line items.
                    </div>
                    <EventHintsSettings />
                </TabsContent>
            </Tabs>
        </PageContainer>
    );
}
