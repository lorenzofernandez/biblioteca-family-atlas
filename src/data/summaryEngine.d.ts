import type{Book}from'./types';export interface Summary{title:string;text:string;score:number;basis:string;sources:{title:string;url:string}[]}export function build(book:Book):Summary[];
