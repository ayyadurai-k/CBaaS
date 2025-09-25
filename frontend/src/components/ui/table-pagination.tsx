import React from 'react';
import ReactPaginate from 'react-paginate';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface PaginationData {
  count: number;
  next: string | null;
  previous: string | null;
  results: any[];
}

interface TablePaginationProps {
  paginationData: PaginationData;
  currentPage: number;
  pageSize?: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}

export const TablePagination: React.FC<TablePaginationProps> = ({
  paginationData,
  currentPage,
  pageSize = 25,
  onPageChange,
  isLoading = false,
}) => {
  const { count, next, previous } = paginationData;
  const totalPages = Math.ceil(count / pageSize);

  const handlePageClick = (event: { selected: number }) => {
    const newPage = event.selected + 1; // react-paginate uses 0-based indexing
    onPageChange(newPage);
  };

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, count);

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-slate-200 bg-white">
      {/* Items info */}
      <div className="text-sm text-slate-600 order-2 sm:order-1">
        {isLoading ? (
          <span>Loading...</span>
        ) : (
          <span>
            Showing {startItem} to {endItem} of {count} items
          </span>
        )}
      </div>

      {/* Pagination controls */}
      <div className="order-1 sm:order-2">
        <ReactPaginate
          previousLabel={
            <div className="flex items-center gap-1">
              <ChevronLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Previous</span>
            </div>
          }
          nextLabel={
            <div className="flex items-center gap-1">
              <span className="hidden sm:inline">Next</span>
              <ChevronRight className="w-4 h-4" />
            </div>
          }
          breakLabel="..."
          pageCount={totalPages}
          marginPagesDisplayed={1}
          pageRangeDisplayed={3}
          onPageChange={handlePageClick}
          forcePage={currentPage - 1} // react-paginate uses 0-based indexing
          containerClassName="flex items-center gap-1"
          pageClassName="inline-block"
          pageLinkClassName="px-3 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
          activeClassName="bg-blue-600 text-white border-blue-600"
          activeLinkClassName="bg-blue-600 text-white border-blue-600 hover:bg-blue-700"
          previousClassName="inline-block"
          nextClassName="inline-block"
          previousLinkClassName={`px-3 py-2 text-sm border border-slate-300 rounded-lg transition-colors ${
            !previous || isLoading 
              ? 'opacity-50 cursor-not-allowed' 
              : 'hover:bg-slate-50'
          }`}
          nextLinkClassName={`px-3 py-2 text-sm border border-slate-300 rounded-lg transition-colors ${
            !next || isLoading 
              ? 'opacity-50 cursor-not-allowed' 
              : 'hover:bg-slate-50'
          }`}
          disabledClassName="opacity-50 cursor-not-allowed"
          breakClassName="inline-block"
          breakLinkClassName="px-3 py-2 text-sm text-slate-500"
        />
      </div>
    </div>
  );
};