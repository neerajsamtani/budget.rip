import React from 'react';
import { Form, InputGroup } from 'react-bootstrap';

interface TagsFilterProps {
    tagFilter: string;
    setTagFilter: (tag: string) => void;
}

export default function TagsFilter({ tagFilter, setTagFilter }: TagsFilterProps) {
    const handleTagChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setTagFilter(event.target.value);
    }

    return (
        <InputGroup>
            <InputGroup.Text>Tags</InputGroup.Text>
            <Form.Control
                type="text"
                placeholder="Enter tag..."
                value={tagFilter}
                onChange={handleTagChange}
            />
        </InputGroup>
    );
}
