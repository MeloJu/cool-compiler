(* Arquivo com erros léxicos propositais, para demonstrar o tratamento de erros *)
class Main {
   a : String <- "string sem fechar as aspas;

   b : Int <- 5 $ 3;

   c : String <- "ok";
};

(* comentário de bloco nunca fechado
class Outro {
};
