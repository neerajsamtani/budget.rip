import React, { useEffect, useState } from "react";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import axiosInstance from "../utils/axiosInstance";

type PaymentMethod = string
interface PaymentMethodFilterProps {
  paymentMethod: PaymentMethod,
  setPaymentMethod: (paymentMethod: PaymentMethod) => void
}

export default function PaymentMethodFilter({ paymentMethod, setPaymentMethod }: PaymentMethodFilterProps) {

  const [paymentMethods, setPaymentMethods] = useState([])

  useEffect(() => {
    var VITE_API_ENDPOINT = String(import.meta.env.VITE_API_ENDPOINT);
    axiosInstance.get(`${VITE_API_ENDPOINT}api/payment_methods`)
      .then(response => {
        setPaymentMethods(Array.isArray(response.data) ? response.data : []);
      })
      .catch(error => console.log(error));
  }, [])


  return (
    <div className="space-y-2">
      <Label>Payment Method</Label>
      <Select value={paymentMethod} onValueChange={setPaymentMethod}>
        <SelectTrigger>
          <SelectValue placeholder="Select payment method" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="All">All</SelectItem>
          {paymentMethods.map(payment_method => {
            return (<SelectItem value={payment_method} key={payment_method}>{payment_method}</SelectItem>)
          })}
        </SelectContent>
      </Select>
    </div>
  );
}