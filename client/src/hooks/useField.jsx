import React, { useState } from 'react'

export const useField = (type) => {
    const [value, setValue] = useState('')

    const setEmpty = () => {
        setValue('')
    }

    const onChange = (event) => {
        setValue(event.target.value)
    }

    return {
        type,
        value,
        onChange,
        setEmpty
    }
}