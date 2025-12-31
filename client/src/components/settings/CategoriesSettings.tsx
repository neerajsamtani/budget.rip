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
import { Spinner } from "@/components/ui/spinner";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Pencil, Plus, Trash2 } from "lucide-react";
import React, { useState } from "react";
import {
    CategoryOption,
    useCategories,
    useCreateCategory,
    useDeleteCategory,
    useUpdateCategory,
} from "../../hooks/useApi";
import { showErrorToast, showSuccessToast } from "../../utils/toast-helpers";

interface CategoryFormData {
    name: string;
}

const emptyFormData: CategoryFormData = {
    name: "",
};

function CategoryEditor({
    category,
    onSave,
    onCancel,
    isSaving,
}: {
    category: CategoryFormData;
    onSave: (data: CategoryFormData) => void;
    onCancel: () => void;
    isSaving: boolean;
}) {
    const [formData, setFormData] = useState<CategoryFormData>(category);

    const handleSubmit = () => {
        if (!formData.name.trim()) {
            showErrorToast(new Error("Please enter a category name"));
            return;
        }
        onSave(formData);
    };

    return (
        <div className="border rounded-lg p-4 space-y-4 bg-muted/30">
            <div className="space-y-2">
                <Label htmlFor="category-name">Category Name *</Label>
                <Input
                    id="category-name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Groceries"
                />
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

export default function CategoriesSettings() {
    const { data: categories = [], isLoading, error } = useCategories();
    const createMutation = useCreateCategory();
    const updateMutation = useUpdateCategory();
    const deleteMutation = useDeleteCategory();

    const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
    const [isCreating, setIsCreating] = useState(false);
    const [deletingCategoryId, setDeletingCategoryId] = useState<string | null>(null);

    const handleCreate = (data: CategoryFormData) => {
        createMutation.mutate(
            { name: data.name },
            {
                onSuccess: () => {
                    showSuccessToast("Category created", "Success");
                    setIsCreating(false);
                },
                onError: (error) => showErrorToast(error),
            }
        );
    };

    const handleUpdate = (id: string, data: CategoryFormData) => {
        updateMutation.mutate(
            { id, name: data.name },
            {
                onSuccess: () => {
                    showSuccessToast("Category updated", "Success");
                    setEditingCategoryId(null);
                },
                onError: (error) => showErrorToast(error),
            }
        );
    };

    const handleDelete = (id: string) => {
        deleteMutation.mutate(id, {
            onSuccess: () => {
                showSuccessToast("Category deleted", "Success");
                setDeletingCategoryId(null);
            },
            onError: (error) => {
                showErrorToast(error);
                setDeletingCategoryId(null);
            },
        });
    };

    const categoryToFormData = (category: CategoryOption): CategoryFormData => ({
        name: category.name,
    });

    return (
        <div className="space-y-6">
            {/* Add new category button */}
            {!isCreating && (
                <Button onClick={() => setIsCreating(true)} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add New Category
                </Button>
            )}

            {/* Create form */}
            {isCreating && (
                <CategoryEditor
                    category={emptyFormData}
                    onSave={handleCreate}
                    onCancel={() => setIsCreating(false)}
                    isSaving={createMutation.isPending}
                />
            )}

            {/* Categories list */}
            {isLoading ? (
                <div className="flex justify-center py-8">
                    <Spinner size="md" className="text-muted-foreground" />
                </div>
            ) : error ? (
                <div className="text-center py-8 text-destructive">
                    <p>Failed to load categories.</p>
                    <p className="text-sm mt-1">Please try refreshing the page.</p>
                </div>
            ) : categories.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                    <p>No categories configured yet.</p>
                    <p className="text-sm mt-1">Create your first category to start organizing events.</p>
                </div>
            ) : (
                <>
                    {/* Mobile card layout */}
                    <div className="md:hidden space-y-4">
                        {categories.map((category) =>
                            editingCategoryId === category.id ? (
                                <CategoryEditor
                                    key={category.id}
                                    category={categoryToFormData(category)}
                                    onSave={(data) => handleUpdate(category.id, data)}
                                    onCancel={() => setEditingCategoryId(null)}
                                    isSaving={updateMutation.isPending}
                                />
                            ) : (
                                <div
                                    key={category.id}
                                    className="border rounded-lg p-4 flex items-center justify-between"
                                >
                                    <p className="font-medium">{category.name}</p>
                                    <div className="flex gap-1">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => setEditingCategoryId(category.id)}
                                        >
                                            <Pencil className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => setDeletingCategoryId(category.id)}
                                            disabled={deleteMutation.isPending}
                                        >
                                            <Trash2 className="h-4 w-4 text-destructive" />
                                        </Button>
                                    </div>
                                </div>
                            )
                        )}
                    </div>

                    {/* Desktop table layout */}
                    <div className="hidden md:block">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead className="w-24">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {categories.map((category) =>
                                    editingCategoryId === category.id ? (
                                        <TableRow key={category.id}>
                                            <TableCell colSpan={2} className="p-0">
                                                <div className="p-4">
                                                    <CategoryEditor
                                                        category={categoryToFormData(category)}
                                                        onSave={(data) => handleUpdate(category.id, data)}
                                                        onCancel={() => setEditingCategoryId(null)}
                                                        isSaving={updateMutation.isPending}
                                                    />
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        <TableRow key={category.id}>
                                            <TableCell className="font-medium">{category.name}</TableCell>
                                            <TableCell>
                                                <div className="flex gap-1">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => setEditingCategoryId(category.id)}
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => setDeletingCategoryId(category.id)}
                                                        disabled={deleteMutation.isPending}
                                                    >
                                                        <Trash2 className="h-4 w-4 text-destructive" />
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    )
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </>
            )}

            {/* Delete confirmation dialog */}
            <AlertDialog open={deletingCategoryId !== null} onOpenChange={(open) => !open && setDeletingCategoryId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Category</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete this category? Events using this category will retain their category reference.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={() => deletingCategoryId && handleDelete(deletingCategoryId)}
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
