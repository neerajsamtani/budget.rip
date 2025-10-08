import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import React from 'react';

interface TagsFilterProps {
    tagFilter: string;
    // eslint-disable-next-line no-unused-vars
    setTagFilter: (tag: string) => void;
}

export default function TagsFilter({ tagFilter, setTagFilter }: TagsFilterProps) {
    const handleTagChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setTagFilter(event.target.value);
    }

    return (
        <div className="space-y-2">
            <Label className="text-sm font-medium text-foreground">Tags</Label>
            <Input
                type="text"
                placeholder="Search by tag..."
                value={tagFilter}
                onChange={handleTagChange}
                className="w-full h-9"
            />
        </div>
    );
}
