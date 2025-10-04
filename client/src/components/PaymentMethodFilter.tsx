import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import React, { useEffect, useState } from "react";
import axiosInstance from "../utils/axiosInstance";
import { showErrorToast } from "../utils/toast-helpers";

type PaymentMethod = string
interface PaymentMethodFilterProps {
  paymentMethod: PaymentMethod,
  // eslint-disable-next-line no-unused-vars
  setPaymentMethod: (paymentMethod: PaymentMethod) => void
}

export default function PaymentMethodFilter({ paymentMethod, setPaymentMethod }: PaymentMethodFilterProps) {

  const [paymentMethods, setPaymentMethods] = useState([])

  useEffect(() => {
    axiosInstance.get(`api/payment_methods`)
      .then(response => {
        setPaymentMethods(Array.isArray(response.data) ? response.data : []);
      })
      .catch(showErrorToast);
  }, [])


  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium text-foreground">Payment Method</Label>
      <Select value={paymentMethod} onValueChange={setPaymentMethod}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select payment method" />
        </SelectTrigger>
        <SelectContent className="bg-white border">
          <SelectItem value="All">All</SelectItem>
          {paymentMethods.map(payment_method => {
            return (<SelectItem value={payment_method} key={payment_method}>{payment_method}</SelectItem>)
          })}
        </SelectContent>
      </Select>
    </div>
  );
}