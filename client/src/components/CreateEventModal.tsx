import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ResponsiveDialog, useIsMobile } from "@/components/ui/responsive-dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import React, { useEffect, useRef, useState } from 'react';
import { Body } from "../components/ui/typography";
import { LineItemInterface, useLineItems, useLineItemsDispatch } from "../contexts/LineItemsContext";
import { CreateEventData, useCategories, useCreateEvent, useEvaluateEventHints, useLineItems as useLineItemsQuery, useTags } from '../hooks/useApi';
import { useField } from '../hooks/useField';
import { calculateEventTotal } from '../utils/eventHelpers';
import { CurrencyFormatter } from '../utils/formatters';
import defaultNameCleanup from '../utils/stringHelpers';
import { showErrorToast, showSuccessToast } from '../utils/toast-helpers';
import { Option } from './Autocomplete';
import { Tag, TagsField } from './TagsField';
import { Spinner } from './ui/spinner';

interface CreateEventModalContentProps {
  initialName: string;
  initialCategory: string;
  initialDate: string;
  initialIsDuplicateTransaction: boolean;
  initialTags: string[];
  selectedLineItems: LineItemInterface[];
  selectedLineItemIds: string[];
  onClose: () => void;
  onSubmit: (draft: CreateEventData) => void;
  isLoadingHints: boolean;
  canSubmit: boolean;
  reconciliationMessage?: React.ReactNode;
}

interface FailedEventSubmission {
  id: string;
  draft: CreateEventData;
  error: unknown;
}

type ReconciliationState = 'idle' | 'checking' | 'ready' | 'error';

/**
 * Inner component that manages form state. Uses key prop from parent to reset
 * when initial values change, eliminating the need for effects to sync state.
 */
function CreateEventModalContent({
  initialName,
  initialCategory,
  initialDate,
  initialIsDuplicateTransaction,
  initialTags,
  selectedLineItems,
  selectedLineItemIds,
  onClose,
  onSubmit,
  isLoadingHints,
  canSubmit,
  reconciliationMessage,
}: CreateEventModalContentProps) {
  // Form fields initialize with props - when parent changes the key, this component
  // remounts with fresh state using the new initial values
  const name = useField<string>("text", initialName);
  const category = useField("select", initialCategory);
  const date = useField<string>("date", initialDate);
  const isDuplicateTransaction = useField<boolean>("checkbox", initialIsDuplicateTransaction);
  const [tags, setTags] = useState<Tag[]>(() => initialTags.map(tag => ({ id: tag, text: tag })));

  const { data: existingTags, isLoading: isLoadingTags } = useTags();
  const { data: categories = [], isLoading: isLoadingCategories, isError: isCategoriesError } = useCategories();

  const tagOptions: Option[] = (existingTags || [])
    .filter(tag => !tags.some(t => t.text === tag.name))
    .map(tag => ({ value: tag.id, label: tag.name }));

  const handleTagSelect = (option: Option) => {
    if (!tags.some(tag => tag.text === option.label)) {
      setTags([...tags, { id: option.value, text: option.label }]);
    }
  };

  const removeTag = (tagId: string) => {
    setTags(tags.filter(tag => tag.id !== tagId));
  };

  const disableSubmit = name.value === "" || category.value === "" || category.value === "All" || selectedLineItemIds.length === 0;

  const total = React.useMemo(() => {
    return calculateEventTotal(selectedLineItems, isDuplicateTransaction.value);
  }, [selectedLineItems, isDuplicateTransaction.value]);

  const createEvent = () => {
    const newEvent = {
      name: name.value,
      category: category.value,
      date: date.value || undefined,
      line_items: selectedLineItemIds,
      is_duplicate_transaction: isDuplicateTransaction.value,
      tags: tags.map(tag => tag.text)
    };
    onSubmit(newEvent);
  };

  const isMobile = useIsMobile();

  if (isLoadingCategories || isLoadingHints) {
    return (
      <div className="space-y-6 py-4 flex justify-center">
        <Spinner size="sm" className="text-muted-foreground" />
      </div>
    );
  } else if (isCategoriesError) {
    // We can swallow a hints error, but not a categories error
    return (
      <div className="space-y-6 py-4 flex justify-center">
        <Body className="text-sm text-destructive">Internal Error: Failed to load categories. Please try again later.</Body>
      </div>
    );
  } else {
    return (
      <>
        {reconciliationMessage}
        <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-1 pt-4 pb-4 -mx-1">
          <div className="space-y-3">
            <Label htmlFor="event-name" className="text-sm font-medium text-foreground">
              Event Name
            </Label>
            <div className="relative">
              <Input
                id="event-name"
                type={name.type}
                value={name.value}
                onChange={name.onChange}
                className="w-full"
                placeholder="Enter a descriptive name for this event"
              />
            </div>
          </div>

          <div className="space-y-3">
            <Label id="category-label" className="text-sm font-medium text-foreground">
              Category
            </Label>
            <Select value={category.value} onValueChange={(value) => category.setCustomValue(value)}>
              <SelectTrigger className="w-full" aria-labelledby="category-label">
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent className="bg-white border">
                {categories.map(cat => (
                  <SelectItem key={cat.id} value={cat.name}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <TagsField
            id="event-tags"
            tags={tags}
            tagOptions={tagOptions}
            isLoading={isLoadingTags}
            onRemoveTag={removeTag}
            onAddTag={handleTagSelect}
          />

          <div className="space-y-3">
            <Label htmlFor="override-date-input" className="text-sm font-medium text-foreground">
              Override Date (optional)
            </Label>
            <Input
              id="override-date-input"
              type={date.type}
              value={date.value}
              onChange={date.onChange}
              className="w-full"
            />
          </div>

          <div className="flex items-center space-x-3 p-4 bg-muted rounded-lg">
            <Checkbox
              id="duplicate-transaction"
              checked={isDuplicateTransaction.value}
              onCheckedChange={() => isDuplicateTransaction.setCustomValue(!isDuplicateTransaction.value)}
              className="border-primary data-[state=checked]:bg-primary"
            />
            <div className="space-y-1">
              <Label htmlFor="duplicate-transaction" className="text-sm font-medium text-foreground cursor-pointer">
                Duplicate Transaction
              </Label>
              <Body className="text-muted-foreground text-xs">
                Check this if the transaction amount is double what it should be
              </Body>
            </div>
          </div>
        </div>

        <div className={`flex shrink-0 pt-4 border-t border-muted ${isMobile ? "flex-col gap-3" : "items-center justify-between"}`}>
          <div className="bg-muted px-4 py-2 rounded-lg">
            <Body className="text-sm font-medium text-foreground">
              Total: <span className="text-primary font-semibold">{CurrencyFormatter.format(total)}</span>
            </Body>
          </div>
          <div className={`flex gap-3 ${isMobile ? "flex-col" : ""}`}>
            <Button onClick={onClose} variant="secondary" className={isMobile ? "w-full" : "min-w-[100px]"}>
              Cancel
            </Button>
            <Button
              onClick={createEvent}
              disabled={disableSubmit || !canSubmit}
              className={isMobile ? "w-full" : "min-w-[100px]"}
            >
              Create Event
            </Button>
          </div>
        </div>
      </>
    );
  }
}

/**
 * Parent component that handles data fetching and computes initial form values.
 * Uses a key prop to reset the inner component when values should change.
 */
export default function CreateEventModal({ show, onHide }: { show: boolean, onHide: () => void }) {
  const { lineItems } = useLineItems();
  const lineItemsDispatch = useLineItemsDispatch();
  const createEventMutation = useCreateEvent();
  const { refetch: refetchReview } = useLineItemsQuery({ onlyLineItemsToReview: true, enabled: false });
  const submissionNumber = useRef(0);
  const failedSubmissionsRef = useRef<FailedEventSubmission[]>([]);
  const [, setFailedSubmissions] = useState<FailedEventSubmission[]>([]);
  const [recoveryDraft, setRecoveryDraft] = useState<FailedEventSubmission | null>(null);
  const [reconciliationState, setReconciliationState] = useState<ReconciliationState>('idle');
  const [reconciliationAttempt, setReconciliationAttempt] = useState(0);
  const [reconciledLineItems, setReconciledLineItems] = useState<LineItemInterface[]>([]);
  // Toast actions outlive their render; read the current dialog state before replacing a draft.
  const dialogOpenRef = useRef(show);
  dialogOpenRef.current = show || recoveryDraft !== null;

  const selectedLineItemsFromReview = (lineItems || []).filter(lineItem => lineItem.isSelected);
  const selectedLineItemIdsFromReview = selectedLineItemsFromReview.map(lineItem => lineItem.id);
  const selectedLineItemIds = recoveryDraft?.draft.line_items ?? selectedLineItemIdsFromReview;
  const selectedLineItems = recoveryDraft
    ? selectedLineItemIds
      .map(lineItemId => reconciledLineItems.find(lineItem => lineItem.id === lineItemId))
      .filter((lineItem): lineItem is LineItemInterface => !!lineItem)
    : selectedLineItemsFromReview;
  const isRecovery = recoveryDraft !== null;

  // Fetch prefill suggestion from server when line items are selected
  const { data: prefillSuggestion, isLoading: isLoadingHints, isError: isHintsError } = useEvaluateEventHints(
    selectedLineItemIds,
    selectedLineItemIds.length > 0 && !isRecovery
  );

  // Show error toast when hints fail to load
  useEffect(() => {
    if (show && isHintsError) {
      showErrorToast("Failed to load event hints. Using default name.");
    }
  }, [show, isHintsError]);

  useEffect(() => {
    if (!recoveryDraft) {
      setReconciliationState('idle');
      return;
    }

    let isCurrent = true;
    setReconciliationState('checking');
    setReconciledLineItems([]);
    refetchReview({ throwOnError: true })
      .then(result => {
        if (!isCurrent) return;
        if (result.status !== 'success' || result.fetchStatus !== 'idle' || !result.data) {
          setReconciliationState('error');
          return;
        }
        setReconciledLineItems(result.data);
        setReconciliationState('ready');
      })
      .catch(() => {
        if (isCurrent) setReconciliationState('error');
      });

    return () => {
      isCurrent = false;
    };
  }, [refetchReview, recoveryDraft?.id, reconciliationAttempt]);

  const unavailableLineItemIds = recoveryDraft
    ? recoveryDraft.draft.line_items.filter(lineItemId => !reconciledLineItems.some(lineItem => lineItem.id === lineItemId))
    : [];

  const updateFailedSubmissions = (nextSubmissions: FailedEventSubmission[]) => {
    failedSubmissionsRef.current = nextSubmissions;
    setFailedSubmissions(nextSubmissions);
  };

  const reopenFailedDraft = (submissionId: string) => {
    const failedSubmission = failedSubmissionsRef.current.find(submission => submission.id === submissionId);
    if (!failedSubmission) return;

    if (dialogOpenRef.current) {
      showErrorToast("Finish or close the current event draft, then reopen this saved draft.", "Draft recovery deferred", {
        duration: Infinity,
        action: { label: "Reopen draft", onClick: () => reopenFailedDraft(submissionId) },
      });
      return;
    }

    updateFailedSubmissions(failedSubmissionsRef.current.filter(submission => submission.id !== submissionId));
    setRecoveryDraft(failedSubmission);
    setReconciliationAttempt(attempt => attempt + 1);
  };

  const handleSubmit = async (draft: CreateEventData) => {
    const submissionId = `event-submission-${++submissionNumber.current}`;
    const draftForRequest: CreateEventData = {
      ...draft,
      line_items: [...draft.line_items],
      tags: [...(draft.tags ?? [])],
    };

    setRecoveryDraft(null);
    onHide();

    try {
      const response = await createEventMutation.mutateAsync(draftForRequest) as { name?: string };
      lineItemsDispatch({ type: "remove_line_items", lineItemIds: draftForRequest.line_items });
      showSuccessToast(response.name || draftForRequest.name, "Created Event");
    } catch (error) {
      const failedSubmission: FailedEventSubmission = {
        id: submissionId,
        draft: draftForRequest,
        error,
      };
      updateFailedSubmissions([...failedSubmissionsRef.current, failedSubmission]);
      showErrorToast(error, "Event could not be saved", {
        duration: Infinity,
        action: {
          label: "Reopen draft",
          onClick: () => reopenFailedDraft(submissionId),
        },
      });
    }
  };

  const handleClose = () => {
    setRecoveryDraft(null);
    onHide();
  };

  const handleUseAvailableLineItems = () => {
    if (!recoveryDraft) return;
    const availableLineItemIds = recoveryDraft.draft.line_items.filter(lineItemId =>
      reconciledLineItems.some(lineItem => lineItem.id === lineItemId)
    );
    setRecoveryDraft({
      ...recoveryDraft,
      draft: {
        ...recoveryDraft.draft,
        line_items: availableLineItemIds,
      },
    });
    setReconciliationState('ready');
  };

  // Compute initial values based on current state
  const computeInitialValues = () => {
    if (isLoadingHints || selectedLineItems.length === 0) {
      return { name: "", category: "" };
    }
    if (prefillSuggestion) {
      return {
        name: prefillSuggestion.name,
        category: prefillSuggestion.category || "",
      };
    }
    return {
      name: defaultNameCleanup(selectedLineItems[0].description),
      category: "",
    };
  };

  const initialValues = computeInitialValues();
  const initialDraft = recoveryDraft?.draft;
  const dialogOpen = show || isRecovery;
  const canSubmit = !isRecovery || (reconciliationState === 'ready' && unavailableLineItemIds.length === 0);

  let reconciliationMessage: React.ReactNode;
  if (isRecovery && reconciliationState === 'checking') {
    reconciliationMessage = <Body className="mt-4 rounded-lg border border-muted bg-muted/40 p-3 text-sm text-muted-foreground">Checking that this draft&apos;s transactions are still available before resubmitting.</Body>;
  } else if (isRecovery && reconciliationState === 'error') {
    reconciliationMessage = (
      <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/5 p-3">
        <Body className="text-sm text-destructive">The draft could not be reconciled with the current review list.</Body>
        <Button variant="secondary" size="sm" className="mt-3" onClick={() => setReconciliationAttempt(attempt => attempt + 1)}>
          Check again
        </Button>
      </div>
    );
  } else if (isRecovery && unavailableLineItemIds.length > 0) {
    reconciliationMessage = (
      <div role="alert" className="mt-4 rounded-lg border border-amber-500/40 bg-amber-50 p-3">
        <Body className="text-sm text-amber-900">
          {unavailableLineItemIds.length === 1 ? 'One transaction' : `${unavailableLineItemIds.length} transactions`} from this draft {unavailableLineItemIds.length === 1 ? 'is' : 'are'} no longer available for review. It may already be assigned, or the earlier request may have succeeded. Reconcile the draft before resubmitting.
        </Body>
        <Button variant="secondary" size="sm" className="mt-3" onClick={handleUseAvailableLineItems} disabled={selectedLineItems.length === 0}>
          Continue with available transactions
        </Button>
      </div>
    );
  } else if (isRecovery) {
    reconciliationMessage = <Body className="mt-4 rounded-lg border border-muted bg-muted/40 p-3 text-sm text-muted-foreground">Draft reconciled. Review the details and explicitly resubmit when ready.</Body>;
  }

  // Key changes when form should reset:
  // - show: reset when modal opens/closes
  // - isLoadingHints: remount when loading finishes to apply prefill
  // - selectedLineItemIds: reset when selection changes
  const formKey = `${show}-${isLoadingHints}-${selectedLineItemIds.join(',')}`;

  const isMobile = useIsMobile();
  const dialogClassName = isMobile
    ? "h-[calc(100dvh-1rem)] overflow-hidden pb-[max(1.5rem,env(safe-area-inset-bottom))]"
    : "w-full !max-w-[42rem]";

  return (
    <ResponsiveDialog open={dialogOpen} onOpenChange={handleClose} className={dialogClassName}>
      <div className="flex shrink-0 flex-col gap-2 pb-4 border-b border-muted">
        <h3 className="text-lg font-semibold text-foreground">New Event Details</h3>
        <p className="text-muted-foreground text-sm">
          Create a financial event from your selected transactions
        </p>
      </div>
      <CreateEventModalContent
        key={recoveryDraft ? recoveryDraft.id : formKey}
        initialName={initialDraft?.name ?? initialValues.name}
        initialCategory={initialDraft?.category ?? initialValues.category}
        initialDate={initialDraft?.date ?? ""}
        initialIsDuplicateTransaction={initialDraft?.is_duplicate_transaction ?? false}
        initialTags={initialDraft?.tags ?? []}
        selectedLineItems={selectedLineItems}
        selectedLineItemIds={selectedLineItemIds}
        onClose={handleClose}
        onSubmit={draft => void handleSubmit(draft)}
        isLoadingHints={isLoadingHints && !isRecovery}
        canSubmit={canSubmit}
        reconciliationMessage={reconciliationMessage}
      />
    </ResponsiveDialog>
  );
}
