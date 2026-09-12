import { AxiosError } from 'axios';
import { toast } from 'sonner';
import { TOAST_DURATION } from '@/constants/ui';

export const showErrorToast = (error: Error | unknown, title = "Error") => {
  let message: string;

  // Check if it's an axios error with a response
  if (error instanceof AxiosError && error.response?.data) {
    // Server may return error in different formats
    const responseData = error.response.data;
    message = responseData.error || responseData.message || error.message;
  } else if (error instanceof Error) {
    message = error.message;
  } else {
    message = String(error);
  }

  toast.error(title, {
    description: message,
    duration: TOAST_DURATION,
  });
};

export const showSuccessToast = (description: string, title = "Success") => {
  toast.success(title, {
    description,
    duration: TOAST_DURATION,
  });
};
