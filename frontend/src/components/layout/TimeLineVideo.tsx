export default function TimeLineVideo(){
    return(<>
     
      {/* Video */}
      <div className="w-full rounded-xl overflow-hidden bg-black">
        <video
          controls
          className="w-full h-auto max-h-[400px] object-contain"
        >
            <source src="https://ik.imagekit.io/ikmedia/example_video.mp4"  type="video/mp4"/> 
         </video>
      </div>

      {/* Timeline */}
      <div className="w-full">
        <div className="relative h-5 rounded-lg bg-[#22325A] flex items-center">
          
          {/* Barra seleccionada */}
          <div className="absolute left-[20%] right-[30%] h-full bg-cyan-500/40 rounded-lg" />

          {/* Handle inicio */}
          <div className="absolute left-[20%] w-4 h-full bg-cyan-400 cursor-ew-resize" />

          {/* Handle fin */}
          <div className="absolute right-[30%] w-4 h-full bg-cyan-400 cursor-ew-resize" />
        </div>
      </div>

    </>)
}