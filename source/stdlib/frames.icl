module frames;
type Point = Record{x:Float64,y:Float64};
fn translate(p:Point,delta:Point)->Point { return {x:p.x+delta.x,y:p.y+delta.y}; }
fn rotate90(p:Point)->Point { return {x:-p.y,y:p.x}; }
fn rotate270(p:Point)->Point { return {x:p.y,y:-p.x}; }
fn scale(p:Point,factor:Float64)->Point { return {x:p.x*factor,y:p.y*factor}; }
