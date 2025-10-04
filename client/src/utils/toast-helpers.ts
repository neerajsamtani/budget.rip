import { toast } from 'sonner';

const TOAST_DURATION = 3500;

export const showErrorToast = (error: Error | unknown, title = "Error") => {
  const message = error instanceof Error ? error.message : String(error);
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
