import { useState } from 'react'

export const useField = (type) => {
    const [value, setValue] = useState('')

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
