import { SelectFilter } from "@/components/ui/select-filter";
import React, { useEffect, useMemo } from "react";
import { usePaymentMethods } from "../hooks/useApi";
import { showErrorToast } from "../utils/toast-helpers";

interface PaymentMethodFilterProps {
  paymentMethod: string,
  // eslint-disable-next-line no-unused-vars
  setPaymentMethod: (paymentMethod: string) => void
}

export default function PaymentMethodFilter({ paymentMethod, setPaymentMethod }: PaymentMethodFilterProps) {
  const { data: fetchedMethods = [], error } = usePaymentMethods();
  // Extract names and add "All" option at the beginning
  const paymentMethodNames = useMemo(
    () => ["All", ...fetchedMethods.map(pm => pm.name)],
    [fetchedMethods]
  );

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
      options={paymentMethodNames}
      placeholder="Select payment method"
    />
  );
}