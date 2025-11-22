import { SelectFilter } from "@/components/ui/select-filter";
import React, { useEffect, useMemo } from "react";
import { usePaymentMethods } from "../hooks/useApi";
import { showErrorToast } from "../utils/toast-helpers";

type PaymentMethod = string
interface PaymentMethodFilterProps {
  paymentMethod: PaymentMethod,
  // eslint-disable-next-line no-unused-vars
  setPaymentMethod: (paymentMethod: PaymentMethod) => void
}

export default function PaymentMethodFilter({ paymentMethod, setPaymentMethod }: PaymentMethodFilterProps) {
  const { data: fetchedMethods = [], error } = usePaymentMethods();
  const paymentMethods = useMemo(() => ["All", ...fetchedMethods], [fetchedMethods]);

  useEffect(() => {
    if (error) {
      showErrorToast(error);
    }
  }, [error]);

  return (
    <SelectFilter
      label="Payment Method"
      value={paymentMethod}
      onChange={setPaymentMethod}
      options={paymentMethods}
      placeholder="Select payment method"
    />
  );
}