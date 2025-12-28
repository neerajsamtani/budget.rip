import { Label } from "@/components/ui/label";
import { useTags } from '@/hooks/useApi';
import React from 'react';
import { AutoComplete, Option } from './Autocomplete';

interface TagsFilterProps {
    tagFilter: string;
    // eslint-disable-next-line no-unused-vars
    setTagFilter: (tag: string) => void;
}

export default function TagsFilter({ tagFilter, setTagFilter }: TagsFilterProps) {
    const { data: tags, isLoading } = useTags();

    const tagOptions: Option[] = (tags || []).map(tag => ({
        value: tag.id,
        label: tag.name,
    }));

    return (
        <div className="space-y-2">
            <Label className="text-sm font-medium text-foreground">Tags</Label>
            <AutoComplete
                options={tagOptions}
                placeholder="Search by tag..."
                value={tagOptions.find(option => option.label === tagFilter)}
                onValueChange={(option) => setTagFilter(option?.label || "")}
                isLoading={isLoading}
            />
        </div>
    );
}
