import React from 'react';
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { AutoComplete, Option } from "./Autocomplete";

export interface Tag {
  id: string;
  text: string;
}

interface TagsFieldProps {
  id: string;
  tags: Tag[];
  tagOptions: Option[];
  isLoading: boolean;
  onRemoveTag: (tagId: string) => void;
  onAddTag: (option: Option) => void;
}

export function TagsField({ id, tags, tagOptions, isLoading, onRemoveTag, onAddTag }: TagsFieldProps) {
  return (
    <div className="space-y-3">
      <Label htmlFor={id} className="text-sm font-medium text-foreground">
        Tags
      </Label>
      <div className="space-y-3">
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tags.map(tag => (
              <Badge
                key={tag.id}
                className="bg-primary text-white hover:bg-primary-dark flex items-center gap-1 px-3 py-1">
                {tag.text}
                <span
                  onClick={() => onRemoveTag(tag.id)}
                  className="ml-1 cursor-pointer hover:text-red-300 font-bold"
                >
                  ×
                </span>
              </Badge>
            ))}
          </div>
        )}
        <AutoComplete
          options={tagOptions}
          placeholder="Type a tag and press Enter to add"
          onValueChange={onAddTag}
          isLoading={isLoading}
          allowCreate={true}
          clearOnSelect={true}
        />
      </div>
    </div>
  );
}
