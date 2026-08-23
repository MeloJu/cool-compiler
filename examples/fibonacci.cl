(*
   Exemplo com let, if/then/else, while e comentários aninhados,
   para exercitar mais tokens do analisador léxico.
*)
class Main inherits IO {

   fib(n : Int) : Int {
      let a : Int <- 0, b : Int <- 1, i : Int <- 0, tmp : Int in {
         while i < n loop {
            tmp <- a + b;
            a <- b;
            b <- tmp;
            i <- i + 1;
         } pool;
         a;
      }
   };

   main() : Object {
      (* (* comentário aninhado *) ainda é comentário *)
      if true then
         out_int(fib(10))
      else
         out_string("nunca chega aqui")
      fi
   };
};
