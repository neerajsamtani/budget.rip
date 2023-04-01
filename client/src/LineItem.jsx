import React, { useState, useEffect } from "react";

export default function LineItem({ lineItem, selectedLineItems, setSelectedLineItems }) {
    const longEnUSFormatter = new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
    const readableDate = longEnUSFormatter.format(lineItem.date * 1000);

    useEffect(() => {
        if (selectedLineItems && !selectedLineItems.includes(lineItem.id)) {
            setIsChecked(false);
        }
    }, [selectedLineItems, lineItem.id])

    const [isChecked, setIsChecked] = useState(false);
    const handleToggle = () => {
        var newSelectedLineItems;
        if (!isChecked) {
            newSelectedLineItems = [...selectedLineItems, lineItem.id]
        } else {
            newSelectedLineItems = selectedLineItems.filter(id => id !== lineItem.id);
        }
        setIsChecked(!isChecked);
        setSelectedLineItems(newSelectedLineItems);
    }

    // February 14, 2020
    return (
        <tr>
            {selectedLineItems && <td><input type="checkbox" checked={isChecked} onChange={handleToggle} /></td>}
            <td>{readableDate}</td>
            <td>{lineItem.payment_method}</td>
            <td>{lineItem.description}</td>
            <td>{lineItem.responsible_party}</td>
            <td>{lineItem.amount}</td>
        </tr>
    )
}