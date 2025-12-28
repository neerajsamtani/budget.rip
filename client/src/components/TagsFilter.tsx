import React, { useMemo } from 'react';
import { Label } from "@/components/ui/label";
import { AutoComplete, Option } from './Autocomplete';
import { useTags } from '@/hooks/useApi';

interface TagsFilterProps {
    tagFilter: string;
    // eslint-disable-next-line no-unused-vars
    setTagFilter: (tag: string) => void;
}

export default function TagsFilter({ tagFilter, setTagFilter }: TagsFilterProps) {
    const { data: tags, isLoading, isError } = useTags();

    const tagOptions: Option[] = useMemo(() => {
        if (isError || !tags) return [];
        return tags.map(tag => ({
            value: tag.id,
            label: tag.name,
        }));
    }, [tags, isError]);

    const currentValue: Option | undefined = useMemo(() => {
        if (!tagFilter) return undefined;
        return tagOptions.find(option => option.label === tagFilter);
    }, [tagFilter, tagOptions]);

    const handleValueChange = (option: Option) => {
        setTagFilter(option.label);
    };

    return (
        <div className="space-y-2">
            <Label className="text-sm font-medium text-foreground">Tags</Label>
            <AutoComplete
                options={tagOptions}
                emptyMessage="No tags found"
                placeholder="Search by tag..."
                value={currentValue}
                onValueChange={handleValueChange}
                isLoading={isLoading}
            />
        </div>
    );
}
