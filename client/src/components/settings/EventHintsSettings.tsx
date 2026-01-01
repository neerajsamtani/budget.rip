import {
    closestCenter,
    DndContext,
    DragEndEvent,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
} from "@dnd-kit/core";
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { GripVertical, Pencil, Plus, Trash2 } from "lucide-react";
import React, { useState } from "react";
import {
    CategoryOption,
    EventHint,
    useCategories,
    useCreateEventHint,
    useDeleteEventHint,
    useEventHints,
    useReorderEventHints,
    useUpdateEventHint,
    useValidateCelExpression
} from "../../hooks/useApi";
import { showErrorToast, showSuccessToast } from "../../utils/toast-helpers";

interface HintFormData {
    name: string;
    cel_expression: string;
    prefill_name: string;
    prefill_category_id: string | null;
    is_active: boolean;
}

const emptyFormData: HintFormData = {
    name: "",
    cel_expression: "",
    prefill_name: "",
    prefill_category_id: null,
    is_active: true,
};

function HintEditor({
    hint,
    categories,
    onSave,
    onCancel,
    isSaving,
}: {
    hint: HintFormData;
    categories: CategoryOption[];
    onSave: (data: HintFormData) => void;
    onCancel: () => void;
    isSaving: boolean;
}) {
    const [formData, setFormData] = useState<HintFormData>(hint);
    const [validationError, setValidationError] = useState<string | null>(null);
    const validateMutation = useValidateCelExpression();

    const handleValidate = () => {
        validateMutation.mutate(formData.cel_expression, {
            onSuccess: (result) => {
                if (result.is_valid) {
                    setValidationError(null);
                    showSuccessToast("Expression is valid", "Validation");
                } else {
                    setValidationError(result.error || "Invalid expression");
                }
            },
        });
    };

    const handleSubmit = () => {
        if (!formData.name || !formData.cel_expression || !formData.prefill_name) {
            showErrorToast(new Error("Please fill in all required fields"));
            return;
        }
        onSave(formData);
    };

    return (
        <div className="border rounded-lg p-4 space-y-4 bg-muted/30">
            <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                    <Label htmlFor="hint-name">Rule Name *</Label>
                    <Input
                        id="hint-name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="e.g., Spotify Subscription"
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="prefill-name">Prefill Event Name *</Label>
                    <Input
                        id="prefill-name"
                        value={formData.prefill_name}
                        onChange={(e) => setFormData({ ...formData, prefill_name: e.target.value })}
                        placeholder="e.g., Spotify"
                    />
                </div>
            </div>

            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <Label htmlFor="cel-expression">CEL Expression *</Label>
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleValidate}
                        disabled={validateMutation.isPending || !formData.cel_expression}
                    >
                        {validateMutation.isPending ? <Spinner size="sm" /> : "Validate"}
                    </Button>
                </div>
                <Textarea
                    id="cel-expression"
                    value={formData.cel_expression}
                    onChange={(e) => {
                        setFormData({ ...formData, cel_expression: e.target.value });
                        setValidationError(null);
                    }}
                    placeholder='e.g., description.contains("Spotify")'
                    className="font-mono text-sm"
                    rows={2}
                />
                {validationError && (
                    <p className="text-sm text-destructive">{validationError}</p>
                )}
                <p className="text-xs text-muted-foreground">
                    Available fields: <code>description</code>, <code>amount</code>, <code>payment_method</code>, <code>responsible_party</code>
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                    <Label htmlFor="prefill-category">Prefill Category</Label>
                    <Select
                        value={formData.prefill_category_id || "none"}
                        onValueChange={(value) =>
                            setFormData({ ...formData, prefill_category_id: value === "none" ? null : value })
                        }
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select a category" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="none">No category</SelectItem>
                            {categories.map((cat) => (
                                <SelectItem key={cat.id} value={cat.id}>
                                    {cat.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
                <div className="flex items-center space-x-2 pt-6">
                    <Switch
                        id="is-active"
                        checked={formData.is_active}
                        onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                    />
                    <Label htmlFor="is-active">Active</Label>
                </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={onCancel} disabled={isSaving}>
                    Cancel
                </Button>
                <Button onClick={handleSubmit} disabled={isSaving}>
                    {isSaving ? <Spinner size="sm" /> : "Save"}
                </Button>
            </div>
        </div>
    );
}

function SortableHintCard({
    hint,
    onEdit,
    onDelete,
    isDeleting,
}: {
    hint: EventHint;
    onEdit: () => void;
    onDelete: () => void;
    isDeleting: boolean;
}) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id: hint.id,
    });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`border rounded-lg p-4 ${!hint.is_active ? "opacity-60" : ""} ${isDragging ? "opacity-50 shadow-lg" : ""}`}
        >
            <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2">
                    <button
                        {...attributes}
                        {...listeners}
                        className="cursor-grab active:cursor-grabbing p-1 -ml-1 text-muted-foreground hover:text-foreground"
                        aria-label="Drag to reorder"
                    >
                        <GripVertical className="h-4 w-4" />
                    </button>
                    <div>
                        <p className="font-medium">{hint.name}</p>
                        <p className="text-sm text-muted-foreground">
                            → {hint.prefill_name}
                            {hint.prefill_category && ` (${hint.prefill_category})`}
                        </p>
                    </div>
                </div>
                <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={onEdit}>
                        <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={onDelete} disabled={isDeleting}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                </div>
            </div>
            <code className="block mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                {hint.cel_expression}
            </code>
        </div>
    );
}

function SortableHintRow({
    hint,
    onEdit,
    onDelete,
    onToggleActive,
    isDeleting,
}: {
    hint: EventHint;
    onEdit: () => void;
    onDelete: () => void;
    onToggleActive: (checked: boolean) => void;
    isDeleting: boolean;
}) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id: hint.id,
    });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
    };

    return (
        <TableRow
            ref={setNodeRef}
            style={style}
            className={`${!hint.is_active ? "opacity-60" : ""} ${isDragging ? "opacity-50 bg-muted" : ""}`}
        >
            <TableCell className="w-8">
                <button
                    {...attributes}
                    {...listeners}
                    className="cursor-grab active:cursor-grabbing p-1 text-muted-foreground hover:text-foreground"
                    aria-label="Drag to reorder"
                >
                    <GripVertical className="h-4 w-4" />
                </button>
            </TableCell>
            <TableCell className="font-medium">{hint.name}</TableCell>
            <TableCell>
                <code className="text-xs bg-muted px-2 py-1 rounded">
                    {hint.cel_expression.length > 40
                        ? hint.cel_expression.substring(0, 40) + "..."
                        : hint.cel_expression}
                </code>
            </TableCell>
            <TableCell>
                {hint.prefill_name}
                {hint.prefill_category && (
                    <span className="text-muted-foreground"> ({hint.prefill_category})</span>
                )}
            </TableCell>
            <TableCell>
                <Switch checked={hint.is_active} onCheckedChange={onToggleActive} />
            </TableCell>
            <TableCell>
                <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={onEdit}>
                        <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={onDelete} disabled={isDeleting}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                </div>
            </TableCell>
        </TableRow>
    );
}

export default function EventHintsSettings() {
    const { data: hints = [], isLoading: isLoadingHints, error: hintsError } = useEventHints();
    const { data: categories = [], isLoading: isLoadingCategories, error: categoriesError } = useCategories();
    const createMutation = useCreateEventHint();
    const updateMutation = useUpdateEventHint();
    const deleteMutation = useDeleteEventHint();
    const reorderMutation = useReorderEventHints();

    const [editingHintId, setEditingHintId] = useState<string | null>(null);
    const [isCreating, setIsCreating] = useState(false);
    const [deletingHintId, setDeletingHintId] = useState<string | null>(null);

    const isLoading = isLoadingHints || isLoadingCategories;
    const error = hintsError || categoriesError;

    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
            const oldIndex = hints.findIndex((h) => h.id === active.id);
            const newIndex = hints.findIndex((h) => h.id === over.id);
            const newOrder = arrayMove(hints, oldIndex, newIndex);
            const hintIds = newOrder.map((h) => h.id);

            reorderMutation.mutate(hintIds, {
                onError: (error) => showErrorToast(error),
            });
        }
    };

    const handleCreate = (data: HintFormData) => {
        createMutation.mutate(
            {
                name: data.name,
                cel_expression: data.cel_expression,
                prefill_name: data.prefill_name,
                prefill_category_id: data.prefill_category_id,
                is_active: data.is_active,
            },
            {
                onSuccess: () => {
                    showSuccessToast("Event hint created", "Success");
                    setIsCreating(false);
                },
                onError: (error) => showErrorToast(error),
            }
        );
    };

    const handleUpdate = (id: string, data: HintFormData) => {
        updateMutation.mutate(
            {
                id,
                name: data.name,
                cel_expression: data.cel_expression,
                prefill_name: data.prefill_name,
                prefill_category_id: data.prefill_category_id,
                is_active: data.is_active,
            },
            {
                onSuccess: () => {
                    showSuccessToast("Event hint updated", "Success");
                    setEditingHintId(null);
                },
                onError: (error) => showErrorToast(error),
            }
        );
    };

    const handleDelete = (id: string) => {
        deleteMutation.mutate(id, {
            onSuccess: () => {
                showSuccessToast("Event hint deleted", "Success");
                setDeletingHintId(null);
            },
            onError: (error) => {
                showErrorToast(error);
                setDeletingHintId(null);
            },
        });
    };

    const hintToFormData = (hint: EventHint): HintFormData => ({
        name: hint.name,
        cel_expression: hint.cel_expression,
        prefill_name: hint.prefill_name,
        prefill_category_id: hint.prefill_category_id,
        is_active: hint.is_active,
    });

    return (
        <div className="space-y-6">
            {/* Add new hint button */}
            {!isCreating && (
                <Button onClick={() => setIsCreating(true)} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add New Hint
                </Button>
            )}

            {/* Create form */}
            {isCreating && (
                <HintEditor
                    hint={emptyFormData}
                    categories={categories}
                    onSave={handleCreate}
                    onCancel={() => setIsCreating(false)}
                    isSaving={createMutation.isPending}
                />
            )}

            {/* Hints list */}
            {isLoading ? (
                <div className="flex justify-center py-8">
                    <Spinner size="md" className="text-muted-foreground" />
                </div>
            ) : error ? (
                <div className="text-center py-8 text-destructive">
                    <p>Failed to load event hints.</p>
                    <p className="text-sm mt-1">Please try refreshing the page.</p>
                </div>
            ) : hints.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                    <p>No event hints configured yet.</p>
                    <p className="text-sm mt-1">Create your first hint to auto-fill event details.</p>
                </div>
            ) : (
                <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                    <SortableContext items={hints.map((h) => h.id)} strategy={verticalListSortingStrategy}>
                        {/* Mobile card layout */}
                        <div className="md:hidden space-y-4">
                            {hints.map((hint) =>
                                editingHintId === hint.id ? (
                                    <HintEditor
                                        key={hint.id}
                                        hint={hintToFormData(hint)}
                                        categories={categories}
                                        onSave={(data) => handleUpdate(hint.id, data)}
                                        onCancel={() => setEditingHintId(null)}
                                        isSaving={updateMutation.isPending}
                                    />
                                ) : (
                                    <SortableHintCard
                                        key={hint.id}
                                        hint={hint}
                                        onEdit={() => setEditingHintId(hint.id)}
                                        onDelete={() => setDeletingHintId(hint.id)}
                                        isDeleting={deleteMutation.isPending}
                                    />
                                )
                            )}
                        </div>

                        {/* Desktop table layout */}
                        <div className="hidden md:block">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-8"></TableHead>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Expression</TableHead>
                                        <TableHead>Prefill</TableHead>
                                        <TableHead>Active</TableHead>
                                        <TableHead className="w-24">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {hints.map((hint) =>
                                        editingHintId === hint.id ? (
                                            <TableRow key={hint.id}>
                                                <TableCell colSpan={6} className="p-0">
                                                    <div className="p-4">
                                                        <HintEditor
                                                            hint={hintToFormData(hint)}
                                                            categories={categories}
                                                            onSave={(data) => handleUpdate(hint.id, data)}
                                                            onCancel={() => setEditingHintId(null)}
                                                            isSaving={updateMutation.isPending}
                                                        />
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        ) : (
                                            <SortableHintRow
                                                key={hint.id}
                                                hint={hint}
                                                onEdit={() => setEditingHintId(hint.id)}
                                                onDelete={() => setDeletingHintId(hint.id)}
                                                onToggleActive={(checked) =>
                                                    updateMutation.mutate({
                                                        id: hint.id,
                                                        is_active: checked,
                                                    })
                                                }
                                                isDeleting={deleteMutation.isPending}
                                            />
                                        )
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </SortableContext>
                </DndContext>
            )}

            {/* Help section */}
            <div className="border rounded-lg p-4 bg-muted/30 space-y-3">
                <h3 className="font-medium">CEL Expression Examples</h3>
                <p className="text-sm text-muted-foreground">
                    String matching is <strong>case-insensitive</strong>. Available fields: <code>description</code>, <code>amount</code>, <code>payment_method</code>, <code>responsible_party</code>.
                </p>
                <div className="text-sm space-y-2 text-muted-foreground">
                    <p>
                        <code className="bg-muted px-1 rounded">description.contains("spotify")</code>
                        {" - "}Matches "SPOTIFY USA", "Spotify Premium", etc.
                    </p>
                    <p>
                        <code className="bg-muted px-1 rounded">amount &gt; 100 && payment_method == "chase credit"</code>
                        {" - "}Matches amounts over $100 paid with Chase Credit
                    </p>
                    <p>
                        <code className="bg-muted px-1 rounded">sum(amount) == 0</code>
                        {" - "}Matches when selected line items sum to zero (transfers)
                    </p>
                    <p>
                        <code className="bg-muted px-1 rounded">all_match(description.contains("uber"))</code>
                        {" - "}Matches when all line items contain "Uber"
                    </p>
                </div>
            </div>

            {/* Delete confirmation dialog */}
            <AlertDialog open={deletingHintId !== null} onOpenChange={(open) => !open && setDeletingHintId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Event Hint</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete this hint? This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={() => deletingHintId && handleDelete(deletingHintId)}
                            disabled={deleteMutation.isPending}
                            className="bg-semantic-error text-white hover:bg-semantic-error-dark focus-visible:ring-semantic-error"
                        >
                            {deleteMutation.isPending ? <Spinner size="sm" /> : "Delete"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
