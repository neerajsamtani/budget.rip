import { ChangeEvent, useState } from 'react';

export type FormField<T> = {
    type: string;
    value: T;
    // eslint-disable-next-line no-unused-vars
    onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
    // eslint-disable-next-line no-unused-vars
    setCustomValue: (value: T) => void;
    setEmpty: () => void;
}

export const useField = <T extends string | number | boolean | readonly string[]>(
    type: string,
    defaultState: T
): FormField<T> => {
    const [value, setValue] = useState<T>(defaultState)

    const setEmpty = () => {
        setValue('' as T)
    }

    const setCustomValue = (newValue: T) => {
        setValue(newValue)
    }

    const onChange = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        setValue(event.target.value as T)
    }

    return {
        type,
        value,
        onChange,
        setCustomValue,
        setEmpty
    }
}