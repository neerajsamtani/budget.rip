import { useState } from 'react'

export const useField = (type, defaultState = "") => {
    const [value, setValue] = useState(defaultState)

    const setEmpty = () => {
        setValue('')
    }

    const setCustomValue = (value) => {
        setValue(value)
    }

    const onChange = (event) => {
        setValue(event.target.value)
    }

    return {
        type,
        value,
        onChange,
        setCustomValue,
        setEmpty
    }
}