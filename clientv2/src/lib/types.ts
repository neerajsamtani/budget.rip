import { CATEGORIES, MONTHS, YEARS } from "./constants";

// Infer the Category type from the CATEGORIES array
export type Category = typeof CATEGORIES[number];

// Infer the Year type from the YEARS array
export type Year = typeof YEARS[number];

// Infer the Year type from the YEARS array
export type Month = typeof MONTHS[number];

export interface LineItemInterface {
    _id: string;
    id: string;
    date: number; // Assuming date is a UNIX timestamp in seconds
    payment_method: string;
    description: string;
    responsible_party: string;
    amount: number;
    isSelected?: boolean; // Optional if not used in this context
}

// Supabase Types

export type Json =
    | string
    | number
    | boolean
    | null
    | { [key: string]: Json | undefined }
    | Json[]

export type Database = {
    public: {
        Tables: {
            accounts: {
                Row: {
                    _id: string
                    account_holder: Json | null
                    authorization: string | null
                    balance: Json | null
                    balance_refresh: Json | null
                    category: string | null
                    created: number | null
                    display_name: string | null
                    id: string | null
                    inferred_balances_refresh: Json | null
                    institution_name: string | null
                    last4: string | null
                    livemode: boolean
                    object: string | null
                    ownership: Json | null
                    ownership_refresh: Json | null
                    permissions: Json | null
                    profile_id: string
                    status: string | null
                    subcategory: string | null
                    subscriptions: Json | null
                    supported_payment_method_types: Json | null
                    transaction_refresh: Json | null
                }
                Insert: {
                    _id: string
                    account_holder?: Json | null
                    authorization?: string | null
                    balance?: Json | null
                    balance_refresh?: Json | null
                    category?: string | null
                    created?: number | null
                    display_name?: string | null
                    id?: string | null
                    inferred_balances_refresh?: Json | null
                    institution_name?: string | null
                    last4?: string | null
                    livemode: boolean
                    object?: string | null
                    ownership?: Json | null
                    ownership_refresh?: Json | null
                    permissions?: Json | null
                    profile_id: string
                    status?: string | null
                    subcategory?: string | null
                    subscriptions?: Json | null
                    supported_payment_method_types?: Json | null
                    transaction_refresh?: Json | null
                }
                Update: {
                    _id?: string
                    account_holder?: Json | null
                    authorization?: string | null
                    balance?: Json | null
                    balance_refresh?: Json | null
                    category?: string | null
                    created?: number | null
                    display_name?: string | null
                    id?: string | null
                    inferred_balances_refresh?: Json | null
                    institution_name?: string | null
                    last4?: string | null
                    livemode?: boolean
                    object?: string | null
                    ownership?: Json | null
                    ownership_refresh?: Json | null
                    permissions?: Json | null
                    profile_id?: string
                    status?: string | null
                    subcategory?: string | null
                    subscriptions?: Json | null
                    supported_payment_method_types?: Json | null
                    transaction_refresh?: Json | null
                }
                Relationships: [
                    {
                        foreignKeyName: "accounts_profile_id_fkey"
                        columns: ["profile_id"]
                        isOneToOne: false
                        referencedRelation: "profiles"
                        referencedColumns: ["id"]
                    },
                ]
            }
            cash_raw_data: {
                Row: {
                    _id: string
                    amount: number | null
                    date: number | null
                    description: string | null
                    person: string | null
                }
                Insert: {
                    _id: string
                    amount?: number | null
                    date?: number | null
                    description?: string | null
                    person?: string | null
                }
                Update: {
                    _id?: string
                    amount?: number | null
                    date?: number | null
                    description?: string | null
                    person?: string | null
                }
                Relationships: []
            }
            events: {
                Row: {
                    _id: string
                    amount: number | null
                    category: string | null
                    date: number | null
                    id: string | null
                    is_duplicate_transaction: boolean | null
                    line_items: Json | null
                    name: string | null
                    profile_id: string
                    tags: string[] | null
                }
                Insert: {
                    _id: string
                    amount?: number | null
                    category?: string | null
                    date?: number | null
                    id?: string | null
                    is_duplicate_transaction?: boolean | null
                    line_items?: Json | null
                    name?: string | null
                    profile_id: string
                    tags?: string[] | null
                }
                Update: {
                    _id?: string
                    amount?: number | null
                    category?: string | null
                    date?: number | null
                    id?: string | null
                    is_duplicate_transaction?: boolean | null
                    line_items?: Json | null
                    name?: string | null
                    profile_id?: string
                    tags?: string[] | null
                }
                Relationships: [
                    {
                        foreignKeyName: "events_profile_id_fkey"
                        columns: ["profile_id"]
                        isOneToOne: false
                        referencedRelation: "profiles"
                        referencedColumns: ["id"]
                    },
                ]
            }
            line_item_to_event: {
                Row: {
                    event_id: string
                    line_item_id: string
                }
                Insert: {
                    event_id: string
                    line_item_id: string
                }
                Update: {
                    event_id?: string
                    line_item_id?: string
                }
                Relationships: [
                    {
                        foreignKeyName: "line_item_to_event_event_id_fkey"
                        columns: ["event_id"]
                        isOneToOne: false
                        referencedRelation: "events"
                        referencedColumns: ["id"]
                    },
                    {
                        foreignKeyName: "line_item_to_event_line_item_id_fkey"
                        columns: ["line_item_id"]
                        isOneToOne: true
                        referencedRelation: "line_items"
                        referencedColumns: ["id"]
                    },
                    {
                        foreignKeyName: "line_item_to_event_line_item_id_fkey"
                        columns: ["line_item_id"]
                        isOneToOne: true
                        referencedRelation: "line_items_to_review"
                        referencedColumns: ["id"]
                    },
                ]
            }
            line_items: {
                Row: {
                    _id: string
                    amount: number | null
                    date: number | null
                    description: string | null
                    id: string | null
                    payment_method: string | null
                    profile_id: string
                    responsible_party: string | null
                }
                Insert: {
                    _id: string
                    amount?: number | null
                    date?: number | null
                    description?: string | null
                    id?: string | null
                    payment_method?: string | null
                    profile_id: string
                    responsible_party?: string | null
                }
                Update: {
                    _id?: string
                    amount?: number | null
                    date?: number | null
                    description?: string | null
                    id?: string | null
                    payment_method?: string | null
                    profile_id?: string
                    responsible_party?: string | null
                }
                Relationships: [
                    {
                        foreignKeyName: "line_items_profile_id_fkey"
                        columns: ["profile_id"]
                        isOneToOne: false
                        referencedRelation: "profiles"
                        referencedColumns: ["id"]
                    },
                ]
            }
            profiles: {
                Row: {
                    avatar_url: string | null
                    created_at: string
                    email: string | null
                    first_name: string | null
                    id: string
                    last_name: string | null
                    updated_at: string | null
                }
                Insert: {
                    avatar_url?: string | null
                    created_at?: string
                    email?: string | null
                    first_name?: string | null
                    id?: string
                    last_name?: string | null
                    updated_at?: string | null
                }
                Update: {
                    avatar_url?: string | null
                    created_at?: string
                    email?: string | null
                    first_name?: string | null
                    id?: string
                    last_name?: string | null
                    updated_at?: string | null
                }
                Relationships: []
            }
            splitwise_raw_data: {
                Row: {
                    _id: string
                    category: Json | null
                    comments_count: number | null
                    cost: string | null
                    created_at: string | null
                    created_by: Json | null
                    creation_method: Json | null
                    currency_code: string | null
                    date: string | null
                    deleted_at: Json | null
                    deleted_by: Json | null
                    description: string | null
                    details: Json | null
                    email_reminder: boolean | null
                    email_reminder_in_advance: number | null
                    expense_bundle_id: Json | null
                    friendship_id: Json | null
                    group_id: Json | null
                    id: number | null
                    next_repeat: Json | null
                    payment: boolean
                    receipt: Json | null
                    repayments: Json | null
                    repeat_interval: Json | null
                    repeats: boolean
                    transaction_confirmed: boolean
                    transaction_id: Json | null
                    transaction_method: string | null
                    updated_at: string | null
                    updated_by: Json | null
                    users: Json | null
                }
                Insert: {
                    _id: string
                    category?: Json | null
                    comments_count?: number | null
                    cost?: string | null
                    created_at?: string | null
                    created_by?: Json | null
                    creation_method?: Json | null
                    currency_code?: string | null
                    date?: string | null
                    deleted_at?: Json | null
                    deleted_by?: Json | null
                    description?: string | null
                    details?: Json | null
                    email_reminder?: boolean | null
                    email_reminder_in_advance?: number | null
                    expense_bundle_id?: Json | null
                    friendship_id?: Json | null
                    group_id?: Json | null
                    id?: number | null
                    next_repeat?: Json | null
                    payment: boolean
                    receipt?: Json | null
                    repayments?: Json | null
                    repeat_interval?: Json | null
                    repeats: boolean
                    transaction_confirmed: boolean
                    transaction_id?: Json | null
                    transaction_method?: string | null
                    updated_at?: string | null
                    updated_by?: Json | null
                    users?: Json | null
                }
                Update: {
                    _id?: string
                    category?: Json | null
                    comments_count?: number | null
                    cost?: string | null
                    created_at?: string | null
                    created_by?: Json | null
                    creation_method?: Json | null
                    currency_code?: string | null
                    date?: string | null
                    deleted_at?: Json | null
                    deleted_by?: Json | null
                    description?: string | null
                    details?: Json | null
                    email_reminder?: boolean | null
                    email_reminder_in_advance?: number | null
                    expense_bundle_id?: Json | null
                    friendship_id?: Json | null
                    group_id?: Json | null
                    id?: number | null
                    next_repeat?: Json | null
                    payment?: boolean
                    receipt?: Json | null
                    repayments?: Json | null
                    repeat_interval?: Json | null
                    repeats?: boolean
                    transaction_confirmed?: boolean
                    transaction_id?: Json | null
                    transaction_method?: string | null
                    updated_at?: string | null
                    updated_by?: Json | null
                    users?: Json | null
                }
                Relationships: []
            }
            stripe_raw_transaction_data: {
                Row: {
                    _id: string
                    account: string | null
                    amount: number | null
                    currency: string | null
                    description: string | null
                    id: string | null
                    livemode: boolean
                    object: string | null
                    status: string | null
                    status_transitions: Json | null
                    transacted_at: number | null
                    transaction_refresh: string | null
                    updated: number | null
                }
                Insert: {
                    _id: string
                    account?: string | null
                    amount?: number | null
                    currency?: string | null
                    description?: string | null
                    id?: string | null
                    livemode: boolean
                    object?: string | null
                    status?: string | null
                    status_transitions?: Json | null
                    transacted_at?: number | null
                    transaction_refresh?: string | null
                    updated?: number | null
                }
                Update: {
                    _id?: string
                    account?: string | null
                    amount?: number | null
                    currency?: string | null
                    description?: string | null
                    id?: string | null
                    livemode?: boolean
                    object?: string | null
                    status?: string | null
                    status_transitions?: Json | null
                    transacted_at?: number | null
                    transaction_refresh?: string | null
                    updated?: number | null
                }
                Relationships: []
            }
            sync_info: {
                Row: {
                    _id: string
                    collection: string | null
                    last_sync_time: string | null
                }
                Insert: {
                    _id: string
                    collection?: string | null
                    last_sync_time?: string | null
                }
                Update: {
                    _id?: string
                    collection?: string | null
                    last_sync_time?: string | null
                }
                Relationships: []
            }
            test_collection: {
                Row: {
                    _id: string
                    age: number | null
                    name: string | null
                }
                Insert: {
                    _id: string
                    age?: number | null
                    name?: string | null
                }
                Update: {
                    _id?: string
                    age?: number | null
                    name?: string | null
                }
                Relationships: []
            }
            users: {
                Row: {
                    _id: string
                    email: string | null
                    first_name: string | null
                    last_name: string | null
                    password_hash: string | null
                    username: string | null
                }
                Insert: {
                    _id: string
                    email?: string | null
                    first_name?: string | null
                    last_name?: string | null
                    password_hash?: string | null
                    username?: string | null
                }
                Update: {
                    _id?: string
                    email?: string | null
                    first_name?: string | null
                    last_name?: string | null
                    password_hash?: string | null
                    username?: string | null
                }
                Relationships: []
            }
            venmo_raw_data: {
                Row: {
                    _id: string
                    _json: Json | null
                    actor: Json | null
                    amount: number | null
                    audience: string | null
                    comments: Json | null
                    date_completed: number | null
                    date_created: number | null
                    date_updated: number | null
                    device_used: string | null
                    id: string | null
                    note: string | null
                    payment_id: string | null
                    payment_type: string | null
                    status: string | null
                    target: Json | null
                }
                Insert: {
                    _id: string
                    _json?: Json | null
                    actor?: Json | null
                    amount?: number | null
                    audience?: string | null
                    comments?: Json | null
                    date_completed?: number | null
                    date_created?: number | null
                    date_updated?: number | null
                    device_used?: string | null
                    id?: string | null
                    note?: string | null
                    payment_id?: string | null
                    payment_type?: string | null
                    status?: string | null
                    target?: Json | null
                }
                Update: {
                    _id?: string
                    _json?: Json | null
                    actor?: Json | null
                    amount?: number | null
                    audience?: string | null
                    comments?: Json | null
                    date_completed?: number | null
                    date_created?: number | null
                    date_updated?: number | null
                    device_used?: string | null
                    id?: string | null
                    note?: string | null
                    payment_id?: string | null
                    payment_type?: string | null
                    status?: string | null
                    target?: Json | null
                }
                Relationships: []
            }
        }
        Views: {
            amount_per_category_per_month: {
                Row: {
                    category: string | null
                    month: string | null
                    total_amount: number | null
                }
                Relationships: []
            }
            line_items_to_review: {
                Row: {
                    _id: string | null
                    amount: number | null
                    date: number | null
                    description: string | null
                    id: string | null
                    payment_method: string | null
                    responsible_party: string | null
                }
                Relationships: []
            }
            net_earnings_per_month: {
                Row: {
                    month: string | null
                    total_amount: number | null
                }
                Relationships: []
            }
        }
        Functions: {
            [_ in never]: never
        }
        Enums: {
            [_ in never]: never
        }
        CompositeTypes: {
            [_ in never]: never
        }
    }
}

type PublicSchema = Database[Extract<keyof Database, "public">]

export type Tables<
    PublicTableNameOrOptions extends
    | keyof (PublicSchema["Tables"] & PublicSchema["Views"])
    | { schema: keyof Database },
    TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
        Database[PublicTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
    ? (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
        Database[PublicTableNameOrOptions["schema"]]["Views"])[TableName] extends {
            Row: infer R
        }
    ? R
    : never
    : PublicTableNameOrOptions extends keyof (PublicSchema["Tables"] &
        PublicSchema["Views"])
    ? (PublicSchema["Tables"] &
        PublicSchema["Views"])[PublicTableNameOrOptions] extends {
            Row: infer R
        }
    ? R
    : never
    : never

export type TablesInsert<
    PublicTableNameOrOptions extends
    | keyof PublicSchema["Tables"]
    | { schema: keyof Database },
    TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
    ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
        Insert: infer I
    }
    ? I
    : never
    : PublicTableNameOrOptions extends keyof PublicSchema["Tables"]
    ? PublicSchema["Tables"][PublicTableNameOrOptions] extends {
        Insert: infer I
    }
    ? I
    : never
    : never

export type TablesUpdate<
    PublicTableNameOrOptions extends
    | keyof PublicSchema["Tables"]
    | { schema: keyof Database },
    TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
    ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
        Update: infer U
    }
    ? U
    : never
    : PublicTableNameOrOptions extends keyof PublicSchema["Tables"]
    ? PublicSchema["Tables"][PublicTableNameOrOptions] extends {
        Update: infer U
    }
    ? U
    : never
    : never

export type Enums<
    PublicEnumNameOrOptions extends
    | keyof PublicSchema["Enums"]
    | { schema: keyof Database },
    EnumName extends PublicEnumNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = PublicEnumNameOrOptions extends { schema: keyof Database }
    ? Database[PublicEnumNameOrOptions["schema"]]["Enums"][EnumName]
    : PublicEnumNameOrOptions extends keyof PublicSchema["Enums"]
    ? PublicSchema["Enums"][PublicEnumNameOrOptions]
    : never

export type CompositeTypes<
    PublicCompositeTypeNameOrOptions extends
    | keyof PublicSchema["CompositeTypes"]
    | { schema: keyof Database },
    CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
        schema: keyof Database
    }
    ? keyof Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof Database }
    ? Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
    : PublicCompositeTypeNameOrOptions extends keyof PublicSchema["CompositeTypes"]
    ? PublicSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never
