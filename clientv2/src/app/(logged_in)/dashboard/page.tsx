import {
  ArrowUpRight,
  CircleUser,
  CreditCard,
  DollarSign
} from "lucide-react"
import Link from "next/link"

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { getAccounts, getAmountPerCategoryPerMonth, getLineItemsToReview } from "@/lib/serverData"
import { toKebabCase } from "@/lib/utils"
import { generateImageMap, ImageMap } from "@/utils/getImageMap"
import { createClient } from "@/utils/supabase/server"

export default async function Dashboard() {
  const supabaseClient = createClient()
  const line_items = await getLineItemsToReview(supabaseClient)
  const apcm = await getAmountPerCategoryPerMonth(supabaseClient)
  const accounts = await getAccounts(supabaseClient)
  const institutionLogos: ImageMap = generateImageMap('institution_logos')

  const total_income = apcm.filter(item => (item.category === 'Income' || item.category === 'Investment')).reduce((acc, curr) => acc - curr.total_amount, 0)
  const total_spending = apcm.filter(item => (item.category !== 'Income' && item.category !== 'Investment')).reduce((acc, curr) => acc + curr.total_amount, 0)
  const total_net_earnings = apcm.reduce((acc, curr) => acc - curr.total_amount, 0)

  // Currency formatter
  const currencyFormatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  return (
    <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
      <div className="grid gap-4 md:grid-cols-2 md:gap-8 lg:grid-cols-4">
        <Card x-chunk="dashboard-01-chunk-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Savings Rate
            </CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{total_income === 0 ? '0.00' : ((total_net_earnings * 100) / total_income).toFixed(2)}%</div>
            {/* <p className="text-xs text-muted-foreground">
              +20.1% from last month
            </p> */}
          </CardContent>
        </Card>
        <Card x-chunk="dashboard-01-chunk-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Income</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currencyFormatter.format(total_income)}</div>
          </CardContent>
        </Card>
        <Card x-chunk="dashboard-01-chunk-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Spending</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currencyFormatter.format(total_spending)}</div>
          </CardContent>
        </Card>
        <Card x-chunk="dashboard-01-chunk-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Earnings</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currencyFormatter.format(total_net_earnings)}</div>
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-4 md:gap-8 lg:grid-cols-2 xl:grid-cols-4">
        <Card
          className="xl:col-span-2" x-chunk="dashboard-01-chunk-4"
        >
          <CardHeader className="flex flex-row items-center">
            <div className="grid gap-2">
              <CardTitle>Transactions</CardTitle>
              <CardDescription>
                Recent transactions to review.
              </CardDescription>
            </div>
            <Button asChild size="sm" className="ml-auto gap-1">
              <Link href="/review">
                View All
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {line_items.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No transactions to review
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {line_items.slice(0, 10).map((line_item) => (
                    <TableRow key={line_item.id}>
                      <TableCell>
                        <div className="font-medium">
                          {line_item.description}
                        </div>
                        <div className="hidden text-sm text-muted-foreground md:inline">
                          {line_item.payment_method === 'Splitwise' || line_item.payment_method === 'Venmo' ? (
                            <div className="flex items-center gap-1">
                              {line_item.payment_method}
                              <CircleUser className="h-4 w-4" />
                              {line_item.responsible_party}
                            </div>
                          ) : (
                            <div className="flex items-center gap-1">
                              <span className="text-sm">{line_item.payment_method}</span>
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{currencyFormatter.format(line_item.amount)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
        <Card className="xl:col-span-2" x-chunk="dashboard-01-chunk-5">
          <CardHeader className="flex flex-row items-center">
            <div className="grid gap-2">
              <CardTitle>Connected Accounts</CardTitle>
              <CardDescription>
                View your linked accounts.
              </CardDescription>
            </div>
            <Button asChild size="sm" className="ml-auto gap-1">
              <Link href="/accounts">
                Manage Accounts
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="grid gap-8">
            {accounts.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No accounts connected
              </p>
            ) : (
              accounts.map((account) => (
                <div className="flex items-center gap-4" key={account.id}>
                  <Avatar className="hidden h-9 w-9 sm:flex">
                    <AvatarImage src={institutionLogos[toKebabCase(account.institution_name)]} alt="Avatar" />
                    <AvatarFallback><CreditCard className="h-4 w-4 text-muted-foreground" /></AvatarFallback>
                  </Avatar>
                  <div className="grid gap-1">
                    <p className="text-sm font-medium leading-none">
                      {account.display_name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {account.institution_name}
                    </p>
                  </div>
                  <div className="ml-auto font-medium">{currencyFormatter.format(account.balance)}</div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
