import { Button } from "@/components/ui/button";
import React from 'react';
import { toast } from "sonner";

export default function ShadcnTestPage() {
  return (
    <div className="container mx-auto p-8 space-y-8">
      <h1 className="text-3xl font-bold text-center mb-8">Shadcn Button Test Page</h1>

      {/* Button Variants */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Button Variants</h2>
        <div className="flex flex-wrap gap-4">
          <Button variant="default">Default</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="link">Link</Button>
        </div>
      </section>

      {/* Button Sizes */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Button Sizes</h2>
        <div className="flex flex-wrap items-center gap-4">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
          <Button size="icon">🚀</Button>
        </div>
      </section>

      {/* Disabled Buttons */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Disabled States</h2>
        <div className="flex flex-wrap gap-4">
          <Button disabled>Default Disabled</Button>
          <Button variant="destructive" disabled>Destructive Disabled</Button>
          <Button variant="outline" disabled>Outline Disabled</Button>
          <Button variant="secondary" disabled>Secondary Disabled</Button>
        </div>
      </section>

      {/* Interactive Examples */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Interactive Examples</h2>
        <div className="flex flex-wrap gap-4">
          <Button onClick={() => alert('Default button clicked!')}>
            Click Me (Default)
          </Button>
          <Button
            variant="destructive"
            onClick={() => alert('Destructive action!')}
          >
            Delete Something
          </Button>
          <Button
            variant="outline"
            onClick={() => alert('Outline button clicked!')}
          >
            Outline Action
          </Button>
        </div>
      </section>

      {/* Button with Icons (using emoji as icons for now) */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Buttons with Icons</h2>
        <div className="flex flex-wrap gap-4">
          <Button>
            ➕ Add Item
          </Button>
          <Button variant="destructive">
            🗑️ Delete
          </Button>
          <Button variant="outline">
            📝 Edit
          </Button>
          <Button variant="secondary">
            💾 Save
          </Button>
        </div>
      </section>

      {/* Button Groups */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Button Groups</h2>
        <div className="flex gap-1">
          <Button variant="outline" className="rounded-r-none">
            First
          </Button>
          <Button variant="outline" className="rounded-none border-l-0">
            Middle
          </Button>
          <Button variant="outline" className="rounded-l-none border-l-0">
            Last
          </Button>
        </div>
      </section>

      {/* Loading States */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Loading States</h2>
        <div className="flex flex-wrap gap-4">
          <Button disabled>
            ⏳ Loading...
          </Button>
          <Button variant="outline" disabled>
            🔄 Processing...
          </Button>
        </div>
      </section>

      {/* Toast Notifications */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Toast Notifications (Sonner)</h2>
        <div className="flex flex-wrap gap-4">
          <Button
            onClick={() => toast.success("Success", {
              description: "This is a success message!",
              duration: 3500,
            })}
          >
            🎉 Success Toast
          </Button>
          <Button
            variant="destructive"
            onClick={() => toast.error("Error", {
              description: "Something went wrong! This is an error message.",
              duration: 5000,
            })}
          >
            ❌ Error Toast
          </Button>
          <Button
            variant="outline"
            onClick={() => toast.info("Info", {
              description: "This is an informational message with some details.",
              duration: 4000,
            })}
          >
            ℹ️ Info Toast
          </Button>
          <Button
            variant="secondary"
            onClick={() => toast("Simple Message")}
          >
            💬 Simple Toast
          </Button>
          <Button
            variant="ghost"
            onClick={() => toast.warning("Warning", {
              description: "This is a warning message. Please be careful!",
              duration: 4500,
            })}
          >
            ⚠️ Warning Toast
          </Button>
        </div>
      </section>
    </div>
  );
}